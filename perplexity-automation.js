const { exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const puppeteer = require('puppeteer');
const readline = require('readline');

// Create interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Configuration
const firefoxProfilePath = "/Users/michael/Library/Application Support/Firefox/Profiles/2e7pi462.MD";
const markdownDirectory = "/Users/michael/Library/CloudStorage/OneDrive-Personal/Documents/2025/projects/forfun/WhereToLive/city-prompts/";
const minWaitTime = 10000; // 10 seconds minimum wait time between requests
const maxWaitTime = 60000; // 60 seconds maximum wait time if rate limited

// Function to open Firefox with specific profile
async function openFirefoxWithProfile() {
  console.log("Opening Firefox with specified profile...");
  return new Promise((resolve, reject) => {
    exec(`open -a Firefox --args -profile "${firefoxProfilePath}"`, (error) => {
      if (error) {
        console.error(`Error opening Firefox: ${error}`);
        reject(error);
      } else {
        console.log("Firefox opened successfully");
        resolve();
      }
    });
  });
}

// Function to get all markdown files from directory
async function getMarkdownFiles() {
  try {
    const files = await fs.readdir(markdownDirectory);
    return files.filter(file => file.endsWith('.md'))
      .map(file => path.join(markdownDirectory, file));
  } catch (error) {
    console.error(`Error reading directory: ${error}`);
    return [];
  }
}

// Function to read markdown file content
async function readMarkdownFile(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    return content;
  } catch (error) {
    console.error(`Error reading file ${filePath}: ${error}`);
    return null;
  }
}

// Function to ask user for input
function askQuestion(query) {
  return new Promise(resolve => rl.question(query, resolve));
}

// Main function to process all markdown files
async function processMarkdownFiles() {
  try {
    // Open Firefox with specific profile
    await openFirefoxWithProfile();
    
    // Wait for Firefox to open
    console.log("Waiting for Firefox to initialize...");
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Launch puppeteer and connect to Firefox
    const browser = await puppeteer.launch({
      product: 'firefox',
      executablePath: '/Applications/Firefox.app/Contents/MacOS/firefox',
      args: [`-profile`, firefoxProfilePath],
      headless: false
    });

    // Get all markdown files
    const mdFiles = await getMarkdownFiles();
    console.log(`Found ${mdFiles.length} markdown files to process`);

    let currentIndex = 0;
    while (currentIndex < mdFiles.length) {
      const file = mdFiles[currentIndex];
      const fileName = path.basename(file);
      console.log(`Processing file ${currentIndex + 1}/${mdFiles.length}: ${fileName}`);

      // Read markdown content
      const content = await readMarkdownFile(file);
      if (!content) {
        console.log(`Skipping ${fileName} due to reading error`);
        currentIndex++;
        continue;
      }

      // Open a new page for each request to avoid any state issues
      const page = await browser.newPage();
      await page.goto('https://www.perplexity.ai/', { waitUntil: 'networkidle2' });

      // Click on the Research div
      try {
        await page.waitForFunction(
          () => {
            const divs = Array.from(document.querySelectorAll('div'));
            return divs.some(div => div.innerText === 'Research');
          },
          { timeout: 10000 }
        );
        
        await page.evaluate(() => {
          const divs = Array.from(document.querySelectorAll('div'));
          const researchDiv = divs.find(div => div.innerText === 'Research');
          if (researchDiv) researchDiv.click();
        });
        
        console.log("Clicked on Research button");
      } catch (error) {
        console.error(`Error clicking Research button: ${error}`);
        await page.close();
        currentIndex++;
        continue;
      }

      // Wait for textarea to be available and paste content
      try {
        await page.waitForSelector('textarea[placeholder="Research anything…"]', { timeout: 10000 });
        await page.type('textarea[placeholder="Research anything…"]', content);
        console.log("Content pasted into textarea");
        
        // Press Enter to submit
        await page.keyboard.press('Enter');
        console.log("Submitted research query");
      } catch (error) {
        console.error(`Error submitting content: ${error}`);
        await page.close();
        currentIndex++;
        continue;
      }

      // Wait for a response or potential rate limit
      console.log("Waiting for response or rate limit notification...");
      await page.waitForTimeout(minWaitTime);

      // Ask user what to do next
      const decision = await askQuestion(
        "\nOptions:\n" +
        "- Press 'n' to move to the next file\n" +
        "- Press 'w' to wait longer (in case of rate limits)\n" +
        "- Press 'p' to pause (press any key to resume)\n" +
        "- Press 'q' to quit\n" +
        "Your choice: "
      );

      switch (decision.toLowerCase()) {
        case 'n':
          console.log("Moving to next file");
          await page.close();
          currentIndex++;
          break;
        case 'w':
          console.log(`Waiting additional ${maxWaitTime/1000} seconds...`);
          await page.waitForTimeout(maxWaitTime);
          await page.close();
          currentIndex++;
          break;
        case 'p':
          console.log("Paused. Press any key to resume...");
          await askQuestion("");
          console.log("Resuming...");
          // Don't close the page or increment the counter to retry the same file
          break;
        case 'q':
          console.log("Quitting...");
          await browser.close();
          rl.close();
          return;
        default:
          console.log("Invalid option, moving to next file");
          await page.close();
          currentIndex++;
      }
    }

    console.log("All markdown files processed");
    await browser.close();
    rl.close();
  } catch (error) {
    console.error(`Error in main process: ${error}`);
    rl.close();
  }
}

// Run the main function
processMarkdownFiles();
