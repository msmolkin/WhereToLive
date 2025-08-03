#!/usr/bin/env python3
import os
import json
import time
import glob
import re
from pathlib import Path
from openai import OpenAI
import argparse
import concurrent.futures
import threading

# Global variable to track total cost
TOTAL_COST = 0.0

class APIKeyRotationError(Exception):
    """Custom exception raised when API key rotation fails or completes."""
    pass

class PerplexityResearcher:
    """
    A class to process city prompts and get detailed research responses using Perplexity's API.
    """
    
    def __init__(self, api_keys, lock, output_dir="./research-results", format="markdown", delay=2.0, cost_threshold=4.0):
        """
        Initialize the PerplexityResearcher with API key and configuration.
        
        Args:
            api_keys (list): List of your Perplexity API keys
            lock (threading.Lock): Lock for thread-safe operations like cost updates
            output_dir (str): Directory to save research results
            format (str): Output format (markdown or json)
            delay (float): Delay in seconds between API requests to avoid rate limiting
            cost_threshold (float): Cost threshold in dollars before rotating API keys
        """
        if isinstance(api_keys, str):
            # Convert single API key to a list
            api_keys = [api_keys]
            self.is_rotate_keys = False
        elif isinstance(api_keys, list):
            # If there's only one key in the list, no rotation
            self.is_rotate_keys = len(api_keys) > 1
        
        self.api_keys = api_keys
        self.current_key_index = 0
        self.cost_threshold = cost_threshold
        self.last_threshold_crossed = 0.0
        self.lock = lock
        
        # Initialize OpenAI client with first API key
        self.client = OpenAI(api_key=self.api_keys[self.current_key_index], base_url="https://api.perplexity.ai")
        
        self.output_dir = output_dir
        self.format = format
        self.delay = delay
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
    
    def rotate_api_key(self):
        """
        Rotate to the next available API key.
        
        Returns:
            bool: True if rotated successfully, exits gracefully if no more keys are available.
        """
        global TOTAL_COST

        if len(self.api_keys) <= 1:
            print("Warning: No additional API keys available for rotation")
            raise APIKeyRotationError("No additional API keys available for rotation")

        # If we're already on the last API key, exit gracefully
        if self.current_key_index == len(self.api_keys) - 1:
            raise APIKeyRotationError("Finished using the last API key. Exiting gracefully. No further searches will be performed.")
        
        old_index = self.current_key_index
        self.current_key_index += 1  # Move to the next API key
        
        # Update the client with the new API key
        self.client = OpenAI(api_key=self.api_keys[self.current_key_index], base_url="https://api.perplexity.ai")
        
        print(f"Rotated API key from #{old_index+1} to #{self.current_key_index+1}")
        self.last_threshold_crossed = (TOTAL_COST // self.cost_threshold) * self.cost_threshold
        return True
    
    def check_rotate_api_key(self):
        """
        Check if we need to rotate the API key based on cost threshold
        """
        global TOTAL_COST
        
        # If we've crossed another multiple of the threshold
        current_threshold = (TOTAL_COST // self.cost_threshold) * self.cost_threshold
        if self.is_rotate_keys and current_threshold > self.last_threshold_crossed:
            print(f"Cost threshold of ${self.cost_threshold} crossed (Total: ${TOTAL_COST:.4f})")
            self.last_threshold_crossed = current_threshold
            return self.rotate_api_key()
        
        return False
    
    def read_prompt_file(self, file_path):
        """
        Read and return the content of a prompt file.
        
        Args:
            file_path (str): Path to the prompt file
            
        Returns:
            str: Content of the prompt file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def extract_city_name(self, filename):
        """
        Extract city and country names from the filename.
        
        Args:
            filename (str): Filename of the format city-country-prompt.md
            
        Returns:
            tuple: (city_name, country_name, clean_filename)
        """
        base_name = os.path.basename(filename)
        match = re.match(r'(.+)-(.+)-prompt\.md', base_name)
        
        if match:
            city = match.group(1).replace('-', ' ').title()
            country = match.group(2).replace('-', ' ').title()
            formatted_name = f"{city}, {country}"
            # Return the original filename prefix as well (without -prompt.md)
            clean_filename = base_name.replace('-prompt.md', '')
            return formatted_name, clean_filename
        else:
            # Just use the filename without extension as a fallback
            clean_name = os.path.splitext(base_name)[0].replace('-prompt', '')
            return clean_name.replace('-', ' ').title(), clean_name
    
    def process_prompt(self, prompt, city_name):
        """
        Send the prompt to Perplexity API and get the research results.
        
        Args:
            prompt (str): The city research prompt
            city_name (str): Name of the city for logging
            
        Returns:
            dict: API response with the research results
        """
        try:
            print(f"Processing research for {city_name}...")
            print(f"This may take 2-4 minutes as Deep Research performs multiple searches and analysis...")
            
            # Create the system message to guide the research
            system_message = (
                "You are an expert researcher specializing in international cost of living and "
                "lifestyle analysis. Provide detailed, factual information with comprehensive "
                "research. Use data from reliable sources and present findings in a structured format "
                "with sections. Include specific numbers, prices, and statistics when available. "
                "Always cite your sources inline with proper attribution."
            )
            
            # Send the request to the Perplexity API
            start_time = time.time()
            response = self.client.chat.completions.create(
                model="sonar-deep-research",  # Using Deep Research model for comprehensive analysis
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more factual responses
                max_tokens=4000   # Adjusted for detailed responses
                # Note: Deep Research automatically runs multiple searches and does 
                # extensive reasoning, so we don't need additional web_search_options
            )
            
            elapsed_time = time.time() - start_time
            print(f"Deep Research completed in {elapsed_time:.2f} seconds for {city_name}")
            
            # Extract and display usage statistics
            if hasattr(response, 'usage'):
                cost = 0
                print(f"Usage stats for {city_name}:")
                if hasattr(response.usage, 'prompt_tokens'):
                    prompt_tokens = response.usage.prompt_tokens
                    print(f"  - Prompt tokens: {prompt_tokens}")
                    # Standard model pricing: $2/1M tokens for input
                    cost += (prompt_tokens / 1000000) * 2
                if hasattr(response.usage, 'completion_tokens'):
                    completion_tokens = response.usage.completion_tokens
                    print(f"  - Completion tokens: {completion_tokens}")
                    # Standard model pricing: $8/1M tokens for output
                    cost += (completion_tokens / 1000000) * 8
                if hasattr(response.usage, 'reasoning_tokens'):
                    reasoning_tokens = response.usage.reasoning_tokens
                    print(f"  - Reasoning tokens: {reasoning_tokens}")
                    # Sonar Deep Research specific: $3/1M tokens for reasoning
                    cost += (reasoning_tokens / 1000000) * 3
                if hasattr(response.usage, 'citation_tokens'):
                    citation_tokens = response.usage.citation_tokens
                    print(f"  - Citation tokens: {citation_tokens}")
                    # Sonar Deep Research specific: $5/1M tokens for citations
                    cost += (citation_tokens / 1000000) * 5
                if hasattr(response.usage, 'num_search_queries'):
                    num_searches = response.usage.num_search_queries
                    print(f"  - Search queries: {num_searches}")
                    # Sonar Deep Research specific: $5 per 1000 searches
                    cost += num_searches * 0.005

            if hasattr(response, 'citations'):
                print(f"  - Number of citations: {len(response.citations)}")

            print(f"  - Estimated cost for {city_name}: ${cost:.4f}")
            global TOTAL_COST
            
            with self.lock:
                TOTAL_COST += cost
            
            # Check if we need to rotate the API key
            self.check_rotate_api_key()
                
            return response
            
        except Exception as e:
            print(f"Error processing prompt for {city_name}: {e}")
            return None
    
    def save_response(self, response, filename_base):
        """
        Save the API response to a file.
        
        Args:
            response: The API response object
            filename_base (str): Base name for the output file
        """
        if response is None:
            return
        
        try:
            # Format the filename
            clean_name = filename_base.replace(', ', '-').replace(' ', '-').lower()
            output_path = os.path.join(self.output_dir, f"{clean_name}.{self.format}")
            print(f"Saving research results to {output_path}")
            
            citations = []
            if hasattr(response, 'citations') and response.citations:
                citations = response.citations
            
            if self.format == "markdown":
                # Extract the content
                content = response.choices[0].message.content
                
                # Check if the content already contains a sources/references section
                has_sources_section = any(header in content.lower() for header in 
                                          ['# sources', '# references', '## sources', '## references',
                                           '### sources', '### references', 'sources:', 'references:'])
                
                # Save the main content
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.write(f"# {filename_base} Living Cost and Lifestyle Research\n\n")
                    file.write(content)
                    
                    # Add a Sources section if we have citations and one doesn't already exist
                    if citations and not has_sources_section:
                        file.write("\n\n## Sources\n\n")
                        for i, url in enumerate(citations, 1):
                            file.write(f"{i}. [{url}]({url})\n")
                
                # Also save the raw response to a JSON file for reference
                raw_response_path = os.path.join(self.output_dir, "raw-responses", f"{clean_name}-raw.json")
                with open(raw_response_path, 'w', encoding='utf-8') as file:
                    # Extract fields we want to save
                    json_data = {
                        'id': response.id,
                        'model': response.model,
                        'created': response.created,
                        'usage': response.usage.model_dump() if hasattr(response.usage, 'model_dump') else vars(response.usage),
                        'citations': citations,
                        'content': content
                    }
                    json.dump(json_data, file, indent=2)
                
                # Save full API response for future reference
                raw_folder = os.path.join(self.output_dir, "raw-responses")
                if not os.path.exists(raw_folder):
                    os.makedirs(raw_folder)
                raw_full_path = os.path.join(raw_folder, f"{clean_name}-full.json")
                with open(raw_full_path, 'w', encoding='utf-8') as rf:
                    json.dump(response.model_dump() if hasattr(response, 'model_dump') else response.model_dump(), rf, indent=2)
            
            elif self.format == "json":
                # Save the full response as JSON
                with open(output_path, 'w', encoding='utf-8') as file:
                    json.dump(response.model_dump(), file, indent=2)

                # Save full API response for future reference
                raw_folder = os.path.join(self.output_dir, "raw-responses")
                if not os.path.exists(raw_folder):
                    os.makedirs(raw_folder)
                raw_full_path = os.path.join(raw_folder, f"{clean_name}-full.json")
                with open(raw_full_path, 'w', encoding='utf-8') as rf:
                    json.dump(response.model_dump() if hasattr(response, 'model_dump') else response, rf, indent=2)
            
            print(f"Saved research results to {output_path}")
            print(f"Number of citations saved: {len(citations)}")
            
        except Exception as e:
            print(f"Error saving response for {filename_base}: {e}")
            import traceback
            traceback.print_exc()
    
    def process_directory(self, prompts_dir="./city-prompts", limit=None):
        """
        Process all prompt files in the specified directory.
        
        Args:
            prompts_dir (str): Directory containing prompt files
            limit (int, optional): Limit the number of files to process
        """
        # Get all markdown files in the prompts directory
        prompt_files = glob.glob(os.path.join(prompts_dir, "*.md"))
        
        if not prompt_files:
            print(f"No prompt files found in {prompts_dir}")
            return
        
        # Sort files for predictable processing order
        prompt_files.sort()
        
        # Apply limit if specified
        if limit and isinstance(limit, int) and limit > 0:
            prompt_files = prompt_files[:limit]
            print(f"Limiting processing to {limit} files")
        
        print(f"Found {len(prompt_files)} prompt files to process")
        
        # Calculate estimated time based on 3 minutes per file (average Deep Research time)
        estimated_minutes = len(prompt_files) * 3
        print(f"Estimated processing time: {estimated_minutes} minutes")
        print(f"Estimated completion time: {time.strftime('%H:%M:%S', time.localtime(time.time() + estimated_minutes * 60))}")
        
        processed_count = 0
        skipped_count = 0
        
        for i, file_path in enumerate(prompt_files):
            # Extract the base filename without path or extension
            base_name = os.path.basename(file_path)
            
            # Expected output filename - directly based on prompt filename
            expected_output_name = base_name.replace('-prompt.md', '').lower() + '.md'
            output_path = os.path.join(self.output_dir, expected_output_name)
            
            # Get city name for display purposes only
            city_name, _ = self.extract_city_name(file_path)
            
            # Debug information
            print(f"Checking for existing file: {output_path}")
            
            if os.path.exists(output_path):
                # Determine age of existing report
                last_mod = os.path.getmtime(output_path)
                age_in_days = (time.time() - last_mod) / (24 * 3600)
                print(f"Found existing report for {city_name}, {age_in_days:.1f} days old")
                
                if age_in_days < 30:
                    print(f"Skipping {city_name} - report generated less than 1 month ago")
                    skipped_count += 1
                    continue
                    
                # Ask user whether to regenerate outdated report
                ans = input(f"Report for {city_name} older than 1 month. Regenerate? [y/N]: ")
                if ans.lower() != 'y':
                    print(f"Skipping {city_name}")
                    skipped_count += 1
                    continue
            
            # Read the prompt content
            prompt_content = self.read_prompt_file(file_path)
            if not prompt_content:
                continue
            
            # Process the prompt with Perplexity API
            response = self.process_prompt(prompt_content, city_name)
            
            # Save the response
            if response:
                self.save_response(response, city_name)
                processed_count += 1
            
            # Delay between API calls to avoid rate limiting
            if i < len(prompt_files) - 1:  # No need to delay after the last request
                print(f"Waiting {self.delay} seconds before next request...")
                time.sleep(self.delay)
        
        print(f"Completed processing {processed_count} prompt files, skipped {skipped_count} files")


def process_files_in_parallel(researchers, prompts_dir, max_workers, delay, limit=None):
    """
    Process multiple prompt files in parallel.
    
    Args:
        researchers: List of PerplexityResearcher instances (one per API key)
        prompts_dir (str): Directory containing prompt files
        max_workers (int): Maximum number of parallel workers in a batch
        delay (float): Delay in seconds between batches
        limit (int, optional): Limit the number of files to process
    """
    # Get all markdown files in the prompts directory
    prompt_files = glob.glob(os.path.join(prompts_dir, "*.md"))
    
    if not prompt_files:
        print(f"No prompt files found in {prompts_dir}")
        return
    
    # Sort files for predictable processing order
    prompt_files.sort()
    
    # Prepare batch of tasks, skipping existing ones
    tasks = []
    skipped_count = 0
    
    output_format = researchers[0].format if researchers else 'md'
    output_dir = researchers[0].output_dir if researchers else './research-results'

    for file_path in prompt_files:
        base_name = os.path.basename(file_path)
        
        expected_output_name = base_name.replace('-prompt.md', '').lower() + f'.{output_format}'
        output_path = os.path.join(output_dir, expected_output_name)
        
        city_name, _ = researchers[0].extract_city_name(file_path) if researchers else ("Unknown", base_name)
        
        if os.path.exists(output_path):
            print(f"Skipping {city_name} - report already exists at {output_path}")
            skipped_count += 1
            continue
            
        # Read the prompt content
        prompt_content = researchers[0].read_prompt_file(file_path) if researchers else None
        if not prompt_content:
            continue
            
        # Add this file to our processing tasks
        tasks.append((file_path, city_name, prompt_content))

    if limit and isinstance(limit, int) and limit > 0:
        tasks = tasks[:limit]

    if not tasks:
        print("No new cities to research.")
        return

    # Calculate estimated time
    num_workers = min(max_workers, len(tasks))
    if num_workers > 0 :
        batches_count = (len(tasks) + num_workers - 1) // num_workers
        estimated_minutes = (len(tasks) * 3) / num_workers
        estimated_delay_minutes = (batches_count - 1) * delay / 60
        total_estimated_minutes = estimated_minutes + estimated_delay_minutes
    else:
        total_estimated_minutes = 0

    
    print(f"\nWill process {len(tasks)} new cities with {num_workers} parallel workers.")
    print(f"Estimated processing time: {total_estimated_minutes:.1f} minutes")
    print(f"Estimated completion time: {time.strftime('%H:%M:%S', time.localtime(time.time() + total_estimated_minutes * 60))}")
    
    processed_count = 0
    
    # Process files in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i, task_data in enumerate(tasks):
            # Distribute tasks among researchers
            researcher_for_task = researchers[i % len(researchers)]
            _, city_name, prompt_content = task_data
            
            # Submit task to executor
            future = executor.submit(process_single_file, researcher_for_task, prompt_content, city_name)
            futures.append(future)
            
        # Wait for all tasks to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result:
                    processed_count += 1
            except Exception as e:
                print(f"Error in processing task: {e}")
    
    print(f"\nCompleted processing {processed_count} prompt files, skipped {skipped_count} files")
    print(f"TOTAL_COST: ${TOTAL_COST:.4f}")


def process_single_file(researcher, prompt_content, city_name):
    """Helper function to process a single file for parallel execution"""
    try:
        response = researcher.process_prompt(prompt_content, city_name)
        if response:
            researcher.save_response(response, city_name)
            return True
    except Exception as e:
        print(f"Error processing {city_name}: {e}")
    return False


def print_estimates(num_files, max_workers, delay):
    """
    Prints the estimated time and cost for the research.
    """
    # Cost estimation constants.
    # NOTE: This is a rough estimate. Actual cost depends on the complexity of the research.
    # We use a conservative number here.
    AVG_COST_PER_CITY = 0.10  # in USD (Adjusted based on more accurate pricing)

    # Time estimation constants
    AVG_MINUTES_PER_CITY = 3.0 # As used elsewhere in the script

    # Total estimated cost
    total_estimated_cost = num_files * AVG_COST_PER_CITY

    # Time estimation
    num_workers = min(max_workers, num_files)
    if num_workers > 0:
        # Number of batches
        batches_count = (num_files + num_workers - 1) // num_workers
        # Time for processing all files, considering parallel execution
        processing_time_minutes = (num_files * AVG_MINUTES_PER_CITY) / num_workers
        # Time for delays between batches is not relevant for a single batch run
        if batches_count > 1:
            delay_minutes = (batches_count - 1) * delay / 60
            total_estimated_minutes = processing_time_minutes + delay_minutes
        else:
            total_estimated_minutes = processing_time_minutes
    else:
        total_estimated_minutes = 0

    print("\n--- Research Plan ---")
    print(f"Cities to research: {num_files}")
    print(f"Parallel workers:   {num_workers}")
    print(f"Estimated time:     ~{total_estimated_minutes:.1f} minutes")
    print(f"Estimated cost:     ~${total_estimated_cost:.2f} (at ~${AVG_COST_PER_CITY}/city)")
    print("---------------------\n")

def main():
    """
    Main function to parse arguments and run the script.
    """
    global TOTAL_COST
    
    parser = argparse.ArgumentParser(description="Process city prompts with Perplexity Deep Research API")
    
    parser.add_argument(
        "--api-key", 
        required=False,
        default=None,
        help="Your Perplexity API key"
    )
    
    parser.add_argument(
        "--api-keys", 
        required=False,
        default=None,
        help="Comma-separated list of Perplexity API keys"
    )
    
    parser.add_argument(
        "--prompts-dir", 
        default="./city-prompts",
        help="Directory containing prompt files (default: ./city-prompts)"
    )
    
    parser.add_argument(
        "--output-dir", 
        default="./research-results",
        help="Directory to save research results (default: ./research-results)"
    )
    
    parser.add_argument(
        "--format", 
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    
    parser.add_argument(
        "--delay", 
        type=float,
        default=60.0,
        help="Delay in seconds between API requests (default: 60.0)"
    )
    
    parser.add_argument(
        "--single", 
        help="Process a single city (provide filename without path)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of cities to process (for testing or budget control)"
    )
    
    parser.add_argument(
        "--parallel",
        type=int,
        default=None, # Default to None, will be set based on keys
        help="Number of parallel queries to run. Defaults to 2x the number of API keys."
    )
    
    parser.add_argument(
        "--cost-threshold",
        type=float,
        default=4.0,
        help="Cost threshold in dollars before rotating API keys (default: 5.0)"
    )
    
    args = parser.parse_args()
    
    # Check if a single API key is provided first, then fall back to api-keys or environment
    api_keys = None
    if args.api_key:
        # If a single API key is provided, use only that one
        api_keys = [args.api_key]
        print("Using single API key provided via --api-key (rotation disabled)")
    elif args.api_keys:
        # If multiple API keys are provided, split them
        api_keys = [key.strip() for key in args.api_keys.split(",")]
        print(f"Using {len(api_keys)} API keys with rotation")
    elif os.environ.get("PERPLEXITY_API_KEYS"):
        # Fall back to environment variable
        env_keys = os.environ.get("PERPLEXITY_API_KEYS")
        api_keys = [key.strip() for key in env_keys.split(",")]
        print(f"Using {len(api_keys)} API keys from environment variable")
    
    if not api_keys:
        parser.error("API keys must be provided via --api-key, --api-keys, or PERPLEXITY_API_KEYS environment variable")
    
    # Determine number of parallel workers
    if args.parallel is None:
        # Default to 2 workers per API key
        max_workers = len(api_keys) * 2
        print(f"Setting parallel workers to {max_workers} (2 per API key)")
    else:
        max_workers = args.parallel

    # --- Pre-run estimation ---
    all_prompt_files = sorted(glob.glob(os.path.join(args.prompts_dir, "*.md")))
    if not all_prompt_files:
        print(f"No prompt files found in {args.prompts_dir}")
        return

    output_format = "md" if args.format == "markdown" else args.format
    files_to_process = []
    for file_path in all_prompt_files:
        base_name = os.path.basename(file_path)
        expected_output_name = base_name.replace('-prompt.md', '').lower() + f'.{output_format}'
        output_path = os.path.join(args.output_dir, expected_output_name)
        if not os.path.exists(output_path):
            files_to_process.append(file_path)

    print(f"\nFound {len(all_prompt_files)} total prompts, {len(files_to_process)} remaining to be processed.")

    if args.limit:
        files_to_process = files_to_process[:args.limit]
        print(f"Will process a maximum of {len(files_to_process)} cities due to --limit.")

    if not files_to_process:
        print("All cities have already been researched. Nothing to do.")
        return
        
    print_estimates(len(files_to_process), max_workers, args.delay)
    # --- End estimation ---

    # Initialize a lock for thread-safe cost updates
    cost_lock = threading.Lock()

    # Create a researcher for each API key
    researchers = [
        PerplexityResearcher(
            api_keys=[key],
            lock=cost_lock,
            output_dir=args.output_dir,
            format=output_format,
            delay=args.delay,
            cost_threshold=args.cost_threshold
        ) for key in api_keys
    ]
    
    # Process a single file or the entire directory
    try:
        if args.single:
            # Note: Single file processing is not parallel and uses the first researcher
            researcher = researchers[0]
            file_path = os.path.join(args.prompts_dir, args.single)
            if os.path.exists(file_path):
                city_name, clean_filename = researcher.extract_city_name(file_path)
                output_path = os.path.join(researcher.output_dir, f"{clean_filename}.{researcher.format}")
                if os.path.exists(output_path):
                    print(f"Skipping {city_name} - report already exists.")
                    return

                prompt_content = researcher.read_prompt_file(file_path)
                if prompt_content:
                    response = researcher.process_prompt(prompt_content, city_name)
                    if response:
                        researcher.save_response(response, city_name)
            else:
                print(f"File not found: {file_path}")
        else:
            process_files_in_parallel(researchers, args.prompts_dir, max_workers, args.delay, limit=args.limit)
    except KeyboardInterrupt:
        print(f"\n\nProcess interrupted by user.")
        print(f"TOTAL_COST: ${TOTAL_COST:.4f}")
        print("Exiting gracefully.")
        exit(0)
    except APIKeyRotationError as e:
        print(f"\n\n{str(e)}")
        print(f"TOTAL_COST: ${TOTAL_COST:.4f}")
        print("Exiting gracefully.")
        exit(0)


if __name__ == "__main__":
    main()
