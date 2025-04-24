#!/usr/bin/env python3
import os
import json
import time
import glob
import re
from pathlib import Path
from openai import OpenAI
import argparse

class PerplexityResearcher:
    """
    A class to process city prompts and get detailed research responses using Perplexity's API.
    """
    
    def __init__(self, api_key, output_dir="./research-results", format="markdown", delay=2.0):
        """
        Initialize the PerplexityResearcher with API key and configuration.
        
        Args:
            api_key (str): Your Perplexity API key
            output_dir (str): Directory to save research results
            format (str): Output format (markdown or json)
            delay (float): Delay in seconds between API requests to avoid rate limiting
        """
        self.client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        self.output_dir = output_dir
        self.format = format
        self.delay = delay
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
    
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
            tuple: (city_name, country_name)
        """
        base_name = os.path.basename(filename)
        match = re.match(r'(.+)-(.+)-prompt\.md', base_name)
        
        if match:
            city = match.group(1).replace('-', ' ').title()
            country = match.group(2).replace('-', ' ').title()
            return f"{city}, {country}"
        else:
            # Just use the filename without extension as a fallback
            return os.path.splitext(base_name)[0].replace('-', ' ').title()
    
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
                print(f"Usage stats for {city_name}:")
                if hasattr(response.usage, 'prompt_tokens'):
                    print(f"  - Prompt tokens: {response.usage.prompt_tokens}")
                if hasattr(response.usage, 'completion_tokens'):
                    print(f"  - Completion tokens: {response.usage.completion_tokens}")
                if hasattr(response.usage, 'reasoning_tokens'):
                    print(f"  - Reasoning tokens: {response.usage.reasoning_tokens}")
                if hasattr(response.usage, 'citation_tokens'):
                    print(f"  - Citation tokens: {response.usage.citation_tokens}")
                if hasattr(response.usage, 'num_search_queries'):
                    print(f"  - Search queries: {response.usage.num_search_queries}")
            
            # Display number of citations if available
            if hasattr(response, 'citations'):
                print(f"  - Number of citations: {len(response.citations)}")
            
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
            output_path = os.path.join(self.output_dir, f"{clean_name}.{"md" if self.format == 'markdown' else self.format}")
            print(f"Saving research results to {output_path}")
            
            if self.format == "markdown":
                # Extract the content
                content = response.choices[0].message.content
                
                # Extract citations if they exist in the response
                citations = []
                if hasattr(response, 'citations') and response.citations:
                    citations = response.citations
                
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
                raw_response_path = os.path.join(self.output_dir, f"{clean_name}-raw.json")
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
                
            elif self.format == "json":
                # Save the full response as JSON
                with open(output_path, 'w', encoding='utf-8') as file:
                    json.dump(response.model_dump(), file, indent=2)
            
            print(f"Saved research results to {output_path}")
            print(f"Number of citations saved: {len(citations) if citations else 0}")
            
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
        
        for i, file_path in enumerate(prompt_files):
            # Extract city name from filename
            city_name = self.extract_city_name(file_path)
            
            # Check if output file already exists to support resuming
            clean_name = city_name.replace(', ', '-').replace(' ', '-').lower()
            output_path = os.path.join(self.output_dir, f"{clean_name}.{self.format}")
            
            if os.path.exists(output_path):
                # Determine age of existing report
                last_mod = os.path.getmtime(output_path)
                if time.time() - last_mod < 30*24*3600:
                    print(f"Skipping {city_name} - report generated less than 1 month ago")
                    continue
                # Ask user whether to regenerate outdated report
                ans = input(f"Report for {city_name} older than 1 month. Regenerate? [y/N]: ")
                if ans.lower() != 'y':
                    print(f"Skipping {city_name}")
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
            
            # Delay between API calls to avoid rate limiting
            if i < len(prompt_files) - 1:  # No need to delay after the last request
                print(f"Waiting {self.delay} seconds before next request...")
                time.sleep(self.delay)
        
        print(f"Completed processing {len(prompt_files)} prompt files")


def main():
    """
    Main function to parse arguments and run the script.
    """
    parser = argparse.ArgumentParser(description="Process city prompts with Perplexity Deep Research API")
    
    parser.add_argument(
        "--api-key", 
        required=True,
        help="Your Perplexity API key"
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
        default=120.0,
        help="Delay in seconds between API requests (default: 120.0)"
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
    
    args = parser.parse_args()
    
    # Initialize the researcher
    researcher = PerplexityResearcher(
        api_key=args.api_key,
        output_dir=args.output_dir,
        format=args.format,
        delay=args.delay
    )
    
    # Process a single file or the entire directory
    if args.single:
        file_path = os.path.join(args.prompts_dir, args.single)
        if os.path.exists(file_path):
            city_name = researcher.extract_city_name(file_path)
            # Skip or confirm regeneration for existing single report
            clean_name = city_name.replace(', ', '-').replace(' ', '-').lower()
            output_path = os.path.join(researcher.output_dir, f"{clean_name}.{researcher.format}")
            if os.path.exists(output_path):
                last_mod = os.path.getmtime(output_path)
                if time.time() - last_mod < 30*24*3600:
                    print(f"Skipping {city_name} - report generated less than 1 month ago")
                    return
                ans = input(f"Report for {city_name} older than 1 month. Regenerate? [y/N]: ")
                if ans.lower() != 'y':
                    print(f"Skipping {city_name}")
                    return
            prompt_content = researcher.read_prompt_file(file_path)
            if prompt_content:
                response = researcher.process_prompt(prompt_content, city_name)
                if response:
                    researcher.save_response(response, city_name)
        else:
            print(f"File not found: {file_path}")
    else:
        researcher.process_directory(args.prompts_dir, limit=args.limit)


if __name__ == "__main__":
    main()
