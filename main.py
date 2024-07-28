import os
import asyncio
from playwright.async_api import async_playwright
import aiohttp
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return "MP3 Generation Service is Running"

async def download_mp3(url, path):
    max_retries = 5
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    with open(path, 'wb') as f:
                        f.write(await response.read())
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retrying download for {url}... (attempt {attempt + 1})")
                    await asyncio.sleep(5)
                else:
                    print(f"Failed to download MP3 file from {url}: {str(e)}")
                    raise

async def process_term(term, translation, output_folder):
    file_path = os.path.join(output_folder, f'{translation}.mp3')

    if os.path.isfile(file_path):
        print(f"MP3 file already exists for {translation}, skipping download.")
        return

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            retry_attempts = 3
            for attempt in range(retry_attempts):
                try:
                    await page.goto("https://ttsfree.com/text-to-speech/hindi-india", timeout=90000)
                    break
                except Exception as e:
                    if attempt < retry_attempts - 1:
                        print(f"Retrying navigation for term '{term}'... (attempt {attempt + 1})")
                        await asyncio.sleep(5)
                    else:
                        print(f"Failed to navigate to the page for term '{term}': {str(e)}")
                        return

            await page.fill('textarea[name="input_text"]', term)
            await page.click('//*[@id="voice_name_bin"]/div[2]')
            await page.click('//*[@id="frm_tts"]/div[2]/div[2]/div[1]/a')

            await page.wait_for_selector('//*[@id="progessResults"]/div[2]/audio', timeout=90000)
            audio_src = await page.get_attribute('//*[@id="progessResults"]/div[2]/audio/source', 'src')

            os.makedirs(output_folder, exist_ok=True)

            await download_mp3(audio_src, file_path)
            print(f"Downloaded MP3 file to {file_path}")

        except Exception as e:
            print(f"Error processing term '{term}': {str(e)}")
        finally:
            await browser.close()

async def main():
    term_mappings = {
        "सौ": "Hundred",
        "हजार": "Thousand",
        "लाख": "Lakh",
        "करोड़": "Crore",
        "वोल्टेज": "Voltage",
        "एम्पीयर": "Ampere",
        "मिलीसेकंड": "Millisecond",
        "मिनट।": "Minute",
        "घंटा": "Hour",
        "मिली": "Milli",
        "रविवार": "Sunday",
        "सोमवार": "Monday",
        "मंगलवार": "Tuesday",
        "बुधवार": "Wednesday",
        "गुरुवार": "Thursday",
        "शुक्रवार": "Friday",
        "शनिवार": "Saturday",
        "आज": "Today",
        "है।": "Is",
        "है, और समय": "IsAndTheTime",
        "बज के": "Oclock",
        "साल": "Year",
        "महीना": "Month",
        "हफ्ता": "Week",
        "दिन": "Day",
        "घड़ी": "Clock",
        "सेकंड": "Second",
        "डिग्री": "Degree",
        "प्रतिशत": "Percentage",
        "परसेंट": "Percent",
        "ग्रेड": "Grade",
        "फैरेनहाइट": "Fahrenheit",
        "सेंटिग्रेड": "Celsius",
        "समीकरण": "Equation",
        "गुणा": "Multiply",
        "भाग": "Divide",
        "जोड़": "Add",
        "घटाना": "Subtract",
        "प्रति": "Per",
        "किलो": "Kilogram",
        "मीटर": "Meter",
        "सेंटीमीटर": "Centimeter",
        "मिलीमीटर": "Millimeter",
        "लिटर": "Liter",
        "गैलन": "Gallon",
        "पाउंड": "Pound",
        "आउंस": "Ounce",
        "कैलोरी": "Calorie",
        "जूल": "Joule",
        "वाट": "Watt",
        "हर्ट्ज़": "Hertz"
    }

    for i in range(101):
        hindi_number = str(i)
        term_mappings[hindi_number] = str(i)

    output_folder = 'mp3_files'
    
    for term, translation in term_mappings.items():
        try:
            await process_term(term, translation, output_folder)
            print(f"Successfully created {translation}.mp3")
        except Exception as e:
            print(f"Error creating MP3 for {term}: {str(e)}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    port = int(os.getenv("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
