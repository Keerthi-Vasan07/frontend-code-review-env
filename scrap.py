from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# 🔧 SETUP
driver = webdriver.Chrome()
driver.maximize_window()

# 🔗 STEP 1: OPEN LOGIN PAGE
driver.get("https://site.pheedloop.com/portal/event/EFTC2026/virtual/lobby")
time.sleep(5)

# 🔐 STEP 2: ENTER EMAIL + PASSWORD

# Try this first (most common)
email = driver.find_element(By.XPATH, "//input[@type='email']")
password = driver.find_element(By.XPATH, "//input[@type='password']")

email.send_keys("keerthivasan2197@gmail.com")
password.send_keys("!&gD8tzF+N")

# 🔘 STEP 3: LOGIN
password.send_keys(Keys.RETURN)

# wait for login to complete
time.sleep(8)

# 🔗 STEP 4: GO TO MAIN SESSIONS PAGE
driver.get("https://site.pheedloop.com/portal/event/EFTC2026/virtual/lobby")
time.sleep(5)

# 🔽 SCROLL (important for loading all sessions)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(3)

# 🔗 STEP 5: COLLECT ALL SESSION LINKS
links = driver.find_elements(By.TAG_NAME, "a")

urls = []
for l in links:
    href = l.get_attribute("href")
    if href and "session" in href.lower():
        urls.append(href)

urls = list(set(urls))
print("Total session pages found:", len(urls))

# 🧠 STEP 6: VISIT EACH PAGE & EXTRACT QUESTIONS
all_questions = set()

for i, url in enumerate(urls):
    print(f"\n[{i+1}/{len(urls)}] Visiting:", url)

    driver.get(url)
    time.sleep(5)

    # scroll again (important)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    elements = driver.find_elements(By.XPATH, "//*[contains(text(),'SCAVENGER HUNT')]")

    for el in elements:
        text = el.text.strip()

        if "SCAVENGER HUNT" in text:
            q = text.split("SCAVENGER HUNT")[-1].strip()

            if len(q) > 10:  # avoid junk
                all_questions.add(q)

# 📋 STEP 7: OUTPUT RESULTS
print("\n🔥 TOTAL UNIQUE QUESTIONS:", len(all_questions))

for q in all_questions:
    print("\n👉", q)

# 💾 SAVE TO FILE
with open("questions.txt", "w", encoding="utf-8") as f:
    for q in all_questions:
        f.write(q + "\n\n")

print("\n✅ Saved to questions.txt")

# ❌ CLOSE
driver.quit()