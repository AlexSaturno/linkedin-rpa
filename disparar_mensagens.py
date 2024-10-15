##### PONTOS IMPORTANTES PARA EDITAR NO ARQUIVO
# 1. Chrome_profile_path: necessário colocar o caminho para o perfil de usuário do chrome
# 2. Caminho para ler o arquivo excel com os perfis: dentro da função main, alterar a variável script_directory
import os
import hashlib
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.common.exceptions import TimeoutException
import pandas as pd

# Path to the provided Chrome profile directory
chrome_profile_path = r"C:\Users\usuario\AppData\Local\Google\Chrome\User Data\Profile 1"  # Incluir path do seu usuário

# Chrome setup with a specific profile
options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={chrome_profile_path}")
options.add_argument("profile-directory=Default")

# Selenium WebDriver configuration
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

# The message to be sent
message = """
Incluir sua mensagem aqui
"""

# Path to the JSON history file
history_file = "historico_envio.json"


# Function to load the history of sent messages
def load_history():
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            return json.load(f)
    return {}


# Function to save the history of sent messages
def save_history(history):
    with open(history_file, "w") as f:
        json.dump(history, f, indent=4)


# Function to generate a message hash for comparison
def generate_message_hash(msg):
    return hashlib.sha256(msg.encode("utf-8")).hexdigest()


# Load the history of sent messages
history = load_history()
message_hash = generate_message_hash(message)

# Control variable to check whether to ask for confirmation for each contact
confirm_all = False


def read_excel_file(file_path):
    df = pd.read_excel(file_path)
    if "URL" not in df.columns:
        raise ValueError(
            "The Excel file must have a column named 'URL' containing the LinkedIn profile URLs."
        )
    return df["URL"].tolist()


# Function to process each LinkedIn profile from the list
def process_profile_urls(profile_urls):
    global history, message_hash

    # Control variable to check whether to ask for confirmation for each contact
    confirm_all = False
    time.sleep(5)
    for profile_url in profile_urls:
        try:
            print(f"Visiting LinkedIn profile: {profile_url}")
            driver.get(profile_url)

            time.sleep(5)  # Allow time for the page to load

            # Try finding all message buttons by the refined XPath
            try:
                # Updated XPath selector to target the 'Message'
                message_buttons = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//button[.//span[text()='Enviar mensagem']]")
                    )
                )
                time.sleep(5)

                # Loop through found buttons and click the one that is displayed
                message_button_clicked = False
                for button in message_buttons:
                    if button.is_displayed():
                        button.click()
                        message_button_clicked = True
                        print("Message button clicked successfully.")
                        time.sleep(5)  # Allow time for the modal to open
                        break

                if not message_button_clicked:
                    print("No visible 'Message' button was found.")
                    continue

            except TimeoutException:
                print(
                    f"Message button not found or not clickable for {profile_url}. Skipping this profile."
                )
                continue
            except Exception as e:
                print(f"Unexpected error when trying to click the message button: {e}")
                continue

            # Verifica se a primeira div (InMail Compose) está presente
            inmail_div_present = (
                len(
                    driver.find_elements(
                        By.CSS_SELECTOR, "div.msg-inmail-compose-form-v2"
                    )
                )
                > 0
            )

            # Se a div InMail estiver presente, feche a caixa de diálogo
            if inmail_div_present:
                print(
                    "InMail Compose dialog detected, closing without sending message."
                )
                close_message_dialog(driver)
            else:
                # Check if the message box is present and insert the message
                message_box = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div.msg-form__contenteditable")
                    )
                )
                message_box.click()
                message_box.clear()
                time.sleep(2)
                message_box.send_keys(message)
                print(f"Message successfully inserted for profile: {profile_url}")

                # Ask for user confirmation before sending if not confirmed for all
                if not confirm_all:
                    user_confirmation = (
                        input(
                            f"Do you want to send the message to {profile_url}? (yes/no/yes to all): "
                        )
                        .strip()
                        .lower()
                    )

                    if user_confirmation == "yes to all":
                        confirm_all = True
                    elif user_confirmation == "no":
                        print(
                            f"Message not sent to {profile_url}. Moving to the next profile."
                        )
                        close_message_dialog(driver)
                        continue
                    elif user_confirmation != "yes":
                        print(
                            f"Invalid input. Message not sent to {profile_url}. Moving to the next profile."
                        )
                        close_message_dialog(driver)
                        continue

                # Send the message
                send_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "button.msg-form__send-button[type='submit']")
                    )
                )
                # Uncomment this line to actually send the message
                send_button.click()
                print(f"Message (would be) sent to profile: {profile_url}")
                time.sleep(5)
                close_message_dialog(driver)

                # Update the history with profile link
                history[profile_url] = {
                    "hash": message_hash,
                    "timestamp": time.time(),
                    "profile_link": profile_url,  # Include the profile link
                }
                save_history(history)
                time.sleep(5)

        except Exception as e:
            print(f"Error processing profile {profile_url}. Error: {e}")
            close_message_dialog(driver)
            continue


def close_message_dialog(driver):
    try:
        # Find all matching close buttons within message dialogs
        close_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    "//div[contains(@class, 'msg-overlay-conversation-bubble')]"
                    "//button[contains(@class, 'msg-overlay-bubble-header__control') or "
                    ".//use[@href='#close-small' or @href='#close-medium']]",
                )
            )
        )

        # Iterate over all found close buttons and attempt to click each one
        for close_button in close_buttons:
            try:
                driver.execute_script("arguments[0].click();", close_button)
                print("Message dialog closed successfully.")
                time.sleep(5)  # Wait a moment for the dialog to close
            except Exception as e:
                print(f"Failed to click on a close button: {e}")

    except TimeoutException as e:
        print("No close buttons found or could not be clicked. {e}")


def export_profiles_to_excel(json_file_path, output_excel_path):
    """
    Reads a JSON file containing profile data, extracts all profile links,
    and exports them to an Excel file.

    :param json_file_path: Path to the JSON file containing profile data.
    :param output_excel_path: Path where the Excel file will be saved.
    """
    # Read the JSON file
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Extract profile links
    profile_links = [
        entry["profile_link"] for entry in data.values() if "profile_link" in entry
    ]

    # Create a DataFrame from the profile links
    df = pd.DataFrame(profile_links, columns=["Profile Link"])

    # Export to Excel
    df.to_excel(output_excel_path, index=False)
    print(f"Profile links have been exported to {output_excel_path}")


# Main function to read profiles from Excel and process them
def main():
    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the Excel file in the same directory as the script
    excel_file_path = os.path.join(script_directory, "list.xlsx")
    profile_urls = read_excel_file(excel_file_path)
    print(f"Total profiles to process: {len(profile_urls)}")

    process_profile_urls(profile_urls)

    print("Processing of LinkedIn profiles completed.")

    # Using the function to read from the uploaded JSON file and export to Excel
    # json_file_path = '/mnt/data/historico_envio.json'
    # output_excel_path = '/mnt/data/exported_profile_links.xlsx'
    # export_profiles_to_excel(json_file_path, output_excel_path)


if __name__ == "__main__":
    main()
