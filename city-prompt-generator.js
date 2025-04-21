// Define our template for generating city prompts
const cityTemplate = `## Comprehensive Living Cost and Lifestyle Research for [CITY_NAME]

Please research and provide detailed information about living costs and lifestyle in [CITY_NAME], [COUNTRY_NAME], covering the following areas:

### 1. Food Prices
- Average monthly grocery cost for individuals and families
- Prices for common grocery items ([FOOD_ITEMS])
- Average cost of eating out ([RESTAURANTS])
- Cost comparison between supermarkets ([SUPERMARKETS]) and local markets ([LOCAL_MARKETS])

### 2. Commuting Costs & Typical Transportation Methods
- Average price of a new and used [PRIMARY_VEHICLE]
- Monthly cost of [PRIMARY_VEHICLE] ownership (insurance, [VEHICLE_EXPENSES])
- Average price of [FUEL_TYPE] (per [FUEL_UNIT])
- Cost of a single [PUBLIC_TRANSPORT] ticket and monthly/annual passes
- Average cost of taxi and [RIDESHARE] services (e.g., [AIRPORT] to [CITY_CENTER])
- **Transportation Habits**: Describe how residents typically get around [CITY_NAME]:
  - What proportion of residents use [TRANSPORT_OPTIONS]?
  - Is [PRIMARY_VEHICLE] ownership common or practical given [TRANSPORT_CONSIDERATIONS]?
  - How comprehensive is the public transportation network?
  - [TRANSPORT_SPECIFICS]
  - [TRANSPORT_CHALLENGES]

### 3. Housing Costs & Rental Process
- Average price to buy a house/apartment (per square meter) in different neighborhoods ([NEIGHBORHOODS])
- Average monthly rent for one- and three-bedroom apartments in different areas
- Average mortgage interest rates and typical monthly mortgage payments
- Required fees and taxes for purchasing property
- Typical upfront costs for renting (security deposit, [RENTAL_COSTS])
- **Local Rental Process**: Describe how the rental system works in [CITY_NAME]:
  - Role of real estate agents
  - Typical lease terms and conditions
  - Documentation requirements for foreigners
  - [RENTAL_SPECIFICS]
  - Popular neighborhoods for expatriates
  - [HOUSING_CONSIDERATIONS]
- Average monthly utilities cost (electricity, water, [ADDITIONAL_UTILITIES])
- [UTILITY_CONSIDERATIONS]

### 4. Political Climate & Safety for Foreigners
- Current political climate in [CITY_NAME] and [COUNTRY_NAME]
- Safety considerations for foreigners, particularly U.S. citizens
- Crime statistics and safer neighborhoods
- Visa requirements and residency options
- Assessment of whether it's feasible for a U.S. citizen to live there safely and legally
- Any special considerations or precautions for foreigners
- Language barriers and English accessibility
- [CULTURAL_CONSIDERATIONS]
- [POLITICAL_SPECIFICS]

Please present all findings in a structured format with tables for easy comparison where appropriate. Include citations for all sources used in your research.
Include US-conversion rates for all currencies and prices.`;

/*
// Function to generate a city prompt from template
function generatePrompt(cityData) {
  return `## Comprehensive Living Cost and Lifestyle Research for ${cityData.CITY_NAME}

Please research and provide detailed information about living costs and lifestyle in ${cityData.CITY_NAME}, ${cityData.COUNTRY_NAME}, covering the following areas:

### 1. Food Prices
- Average monthly grocery cost for individuals and families
- Prices for common grocery items (${cityData.FOOD_ITEMS})
- Average cost of eating out (${cityData.RESTAURANTS})
- Cost comparison between supermarkets (${cityData.SUPERMARKETS}) and local markets (${cityData.LOCAL_MARKETS})

### 2. Commuting Costs & Typical Transportation Methods
- Average price of a new and used ${cityData.PRIMARY_VEHICLE}
- Monthly cost of ${cityData.PRIMARY_VEHICLE} ownership (insurance, ${cityData.VEHICLE_EXPENSES})
- Average price of ${cityData.FUEL_TYPE} (per ${cityData.FUEL_UNIT})
- Cost of a single ${cityData.PUBLIC_TRANSPORT} ticket and monthly/annual passes
- Average cost of taxi and ${cityData.RIDESHARE} services (e.g., ${cityData.AIRPORT} to ${cityData.CITY_CENTER})
- **Transportation Habits**: Describe how residents typically get around ${cityData.CITY_NAME}:
  - What proportion of residents use ${cityData.TRANSPORT_OPTIONS}?
  - Is ${cityData.PRIMARY_VEHICLE} ownership common or practical given ${cityData.TRANSPORT_CONSIDERATIONS}?
  - How comprehensive is the public transportation network?
  - ${cityData.TRANSPORT_SPECIFICS}
  - ${cityData.TRANSPORT_CHALLENGES}

### 3. Housing Costs & Rental Process
- Average price to buy a house/apartment (per square meter) in different neighborhoods (${cityData.NEIGHBORHOODS})
- Average monthly rent for one- and three-bedroom apartments in different areas
- Average mortgage interest rates and typical monthly mortgage payments
- Required fees and taxes for purchasing property
- Typical upfront costs for renting (security deposit, ${cityData.RENTAL_COSTS})
- **Local Rental Process**: Describe how the rental system works in ${cityData.CITY_NAME}:
  - Role of real estate agents
  - Typical lease terms and conditions
  - Documentation requirements for foreigners
  - ${cityData.RENTAL_SPECIFICS}
  - Popular neighborhoods for expatriates
  - ${cityData.HOUSING_CONSIDERATIONS}
- Average monthly utilities cost (electricity, water, ${cityData.ADDITIONAL_UTILITIES})
- ${cityData.UTILITY_CONSIDERATIONS}

### 4. Political Climate & Safety for Foreigners
- Current political climate in ${cityData.CITY_NAME} and ${cityData.COUNTRY_NAME}
- Safety considerations for foreigners, particularly U.S. citizens
- Crime statistics and safer neighborhoods
- Visa requirements and residency options
- Assessment of whether it's feasible for a U.S. citizen to live there safely and legally
- Any special considerations or precautions for foreigners
- Language barriers and English accessibility
- ${cityData.CULTURAL_CONSIDERATIONS}
- ${cityData.POLITICAL_SPECIFICS}

Please present all findings in a structured format with tables for easy comparison where appropriate. Include citations for all sources used in your research.
Include US-conversion rates for all currencies and prices.`;
}
*/

// Function to generate a city-specific prompt
function generateCityPrompt(cityInfo) {
  let prompt = cityTemplate;
  
  // Replace all placeholders with city-specific info
  for (const [key, value] of Object.entries(cityInfo)) {
    const regex = new RegExp(`\\[${key}\\]`, 'g');
    prompt = prompt.replace(regex, value);
  }
  
  return prompt;
}

// Database of city information in city-database.js

const path = require('path');
const fs = require('fs');
const cityDatabase = require('./city-database');
const dir = './city-prompts';


// Function to generate prompts for all cities in the database
function generateAllCityPrompts(cityDatabase) {
  const prompts = {};
  
  for (const city of cityDatabase) {
    prompts[city.CITY_NAME] = generateCityPrompt(city);
  }
  
  return prompts;
}

// Example usage: Access the prompt for a specific city
// console.log(allPrompts["Marrakech"]);

// To add a new city, simply add its information to the cityDatabase
function addCityToDatabase(cityInfo) {
  cityDatabase.push(cityInfo);
  // Return the generated prompt for the new city
  return generateCityPrompt(cityInfo);
}

// Example: Adding a new city
const newCity = {
  CITY_NAME: "Lisbon",
  COUNTRY_NAME: "Portugal",
  // Add all required fields here
  FOOD_ITEMS: "bacalhau, sardines, olive oil, pastéis de nata, wine, cheese, etc.",
  RESTAURANTS: "traditional Portuguese tascas, seafood restaurants, pastry shops (pastelarias), mid-range restaurants",
  SUPERMARKETS: "Continente, Pingo Doce, Lidl",
  LOCAL_MARKETS: "Mercado da Ribeira/Time Out Market, Mercado de Alvalade",
  PRIMARY_VEHICLE: "car",
  VEHICLE_EXPENSES: "road tax, maintenance, parking",
  FUEL_TYPE: "gasoline",
  FUEL_UNIT: "liter",
  PUBLIC_TRANSPORT: "metro/bus/tram",
  RIDESHARE: "ride-hailing",
  AIRPORT: "Lisbon Airport",
  CITY_CENTER: "Baixa/Chiado",
  TRANSPORT_OPTIONS: "metro, buses, historic trams, funiculars, or drive cars",
  TRANSPORT_CONSIDERATIONS: "the hilly terrain and narrow streets in historic neighborhoods",
  TRANSPORT_SPECIFICS: "Historic trams like the famous Tram 28 and funiculars for steep hills",
  TRANSPORT_CHALLENGES: "Limited parking, narrow streets, and steep hills in traditional neighborhoods",
  NEIGHBORHOODS: "Baixa, Chiado, Alfama, Graça, Príncipe Real, etc.",
  RENTAL_COSTS: "agency fees, etc.",
  RENTAL_SPECIFICS: "Traditional Portuguese apartments vs. renovated units",
  HOUSING_CONSIDERATIONS: "Impact of tourism and short-term rentals on housing market",
  ADDITIONAL_UTILITIES: "internet, gas",
  UTILITY_CONSIDERATIONS: "Heating needs in winter despite mild climate (older buildings often lack insulation)",
  CULTURAL_CONSIDERATIONS: "Portuguese customs, fado music culture, and growing expatriate community",
  POLITICAL_SPECIFICS: "Portugal's political stability and NHR (Non-Habitual Resident) tax program"
};

// Add the new city
addCityToDatabase(newCity);
// Generate prompts for all cities
const allPrompts = generateAllCityPrompts(cityDatabase);

// How to export the prompts

// For each city, create the prompt and store it as needed

// Create a folder if it doesn't exist
if (!fs.existsSync(dir)) {
  fs.mkdirSync(dir);
}

for (const [originalCityName, prompt] of Object.entries(allPrompts)) {
  console.log(`Exporting prompt for ${originalCityName}...`);
  // Use your preferred method to save or use each prompt
  // For example, save to a file or send to an API

  // Normalize city name for file naming
  const normalizedCityName = originalCityName.replace(/\s+/g, '-').toLowerCase();

  // Get country name from the city database matching the normalized city name
  const cityData = cityDatabase.find(
    city => city.CITY_NAME.replace(/\s+/g, '-').toLowerCase() === normalizedCityName
  );
  if (!cityData) {
    console.log(`City data for ${originalCityName} not found.`);
    continue;
  }

  // Normalize country name for file naming
  const normalizedCountryName = cityData.COUNTRY_NAME.replace(/\s+/g, '-').toLowerCase();

  // Define the file name and path
  const baseFileName = `${normalizedCityName}-${normalizedCountryName}-prompt.md`;
  const filePath = path.join(dir, baseFileName);

  // Write the prompt to the file
  fs.writeFileSync(filePath, prompt, 'utf8');
  console.log(`Prompt for ${originalCityName} saved to ${filePath}`);
}