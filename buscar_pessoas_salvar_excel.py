##### PONTOS IMPORTANTES PARA EDITAR NO ARQUIVO
# 1. Chrome_profile_path: necessário colocar o caminho para o perfil de usuário do chrome
# 2. Credenciais linkedin: usuário e senha
# 3. Caminho para salvar o arquivo excel gerado: dentro da função "save_urls_to_excel" é necessário ajustar o path
# 4. Pesquisa a ser feita no linkedin: dentro da função main, alterar a variável "search_query"
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import time

# Configurar o ChromeDriver com o perfil do usuário
chrome_profile_path = r"C:\Users\usuario\AppData\Local\Google\Chrome\User Data\Profile 1"  # Alterar para seu perfil
options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={chrome_profile_path}")
options.add_argument("profile-directory=Default")

# Iniciar o WebDriver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

# Credenciais do LinkedIn/Google (substitua com seu e-mail e senha)
username = "username"
password = "password"


# Função para realizar login no LinkedIn usando autenticação do Google
def linkedin_login_google(username, password):
    try:
        # Acessar a página de login do LinkedIn
        driver.get("https://www.linkedin.com/login")
        time.sleep(10)  # Aguarda carregar a página

        # Encontrar e clicar no botão de "Login com Google"
        login_google_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[@class='nsm7Bb-HzV7m-LgbsSe-bN97Pc-sM5MNb oXtfBe-l4eHX']",
                )
            )
        )
        login_google_button.click()
        time.sleep(2)

        # Alternar para a janela do Google Login
        driver.switch_to.window(
            driver.window_handles[-1]
        )  # Muda para a última janela/popup aberta

        # Preencher o e-mail no campo de entrada do Google
        google_email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
        )
        google_email_input.send_keys(username)
        google_email_input.send_keys(Keys.ENTER)
        time.sleep(2)

        # Preencher a senha no campo de entrada do Google
        google_password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        google_password_input.send_keys(password)
        google_password_input.send_keys(Keys.ENTER)
        time.sleep(5)  # Aguarda o login ser processado

        # Alternar de volta para a janela principal do LinkedIn
        driver.switch_to.window(
            driver.window_handles[0]
        )  # Muda para a janela inicial do LinkedIn

        print("Login realizado com sucesso via Google!")
    except TimeoutException:
        print("Erro: não foi possível encontrar os campos de login do Google.")
    except Exception as e:
        print(f"Erro durante o login via Google: {e}")


# Função para realizar login no LinkedIn
def linkedin_login(username, password):
    try:
        # Acessar a página de login do LinkedIn
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)  # Aguarda carregar a página

        # Encontrar o campo de e-mail e senha e preencher
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        email_input.send_keys(username)

        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_input.send_keys(password)

        # Clicar no botão de login
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()
        time.sleep(5)  # Aguarda o login ser processado

        print("Login realizado com sucesso!")
    except TimeoutException:
        print("Erro: não foi possível encontrar os campos de login.")
    except Exception as e:
        print(f"Erro durante o login: {e}")


# Função para realizar uma busca e capturar os URLs dos perfis
def search_and_capture_urls(search_query, max_pages=50):
    search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query}&origin=CLUSTER_EXPANSION"
    driver.get(search_url)
    time.sleep(50)

    profile_urls = []

    for page in range(max_pages):
        print(f"Processing page {page + 1}...")

        # Esperar carregar os resultados
        WebDriverWait(driver, 50).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "li.reusable-search__result-container")
            )
        )

        # Capturar todos os resultados de perfis na página
        profiles = driver.find_elements(By.CSS_SELECTOR, "a.app-aware-link")

        # Adicionar os URLs de cada perfil à lista (remover duplicados)
        for profile in profiles:
            profile_url = profile.get_attribute("href")
            if (
                profile_url
                and "linkedin.com/in/" in profile_url
                and profile_url not in profile_urls
            ):
                profile_urls.append(profile_url)

        # Rolagem automática para o final da página antes de capturar os resultados
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(1, scroll_height, 500):  # Rola de 500 em 500 pixels
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.5)  # Aguardar meio segundo para carregar os elementos

        # Ir para a próxima página
        try:
            next_button = driver.find_element(
                By.XPATH, "//button[contains(@aria-label, 'Avançar')]"
            )
            next_button.click()
            time.sleep(10)
        except Exception as e:
            print(f"Could not find 'Next' button or encountered an error: {e}")
            break  # Sair do loop se não encontrar o botão de próxima página

    # Retornar os URLs capturados
    return profile_urls


# Função para salvar os URLs em um arquivo Excel
def save_urls_to_excel(
    profile_urls,
    excel_file_path=r"seu_path_aqui",
):
    df = pd.DataFrame(profile_urls, columns=["URL"])
    df.to_excel(excel_file_path, index=False)
    print(f"URLs saved to {excel_file_path}")


# Função principal para executar o script
def main():
    # Realizar login no LinkedIn
    linkedin_login(username, password)

    # Executar a busca e capturar URLs
    search_query = "sua_busca_aqui"
    captured_urls = search_and_capture_urls(search_query)

    # Salvar URLs capturados no arquivo Excel
    save_urls_to_excel(captured_urls)

    # Fechar o WebDriver
    driver.quit()


if __name__ == "__main__":
    main()
