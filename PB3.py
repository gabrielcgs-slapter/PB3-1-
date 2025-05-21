from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import time
from selenium.webdriver.common.keys import Keys
import csv
import datetime
import os
import pytz
import smtplib
import email.message
import psutil
import re
import numpy as np

#destinatário = 'gabriel.calazans@ini.fiocruz.br'
destinatário = 'regulatorios@ini.fiocruz.br'

# GABRIEL LOGIN
login = "gabrielcgs12@gmail.com"; senha = "0Dije!c!"

# TANIA LOGIN
#login = "tania.krstic@ini.fiocruz.br"; senha = "987654"

timezone = pytz.timezone('Etc/GMT+3')

for proc in psutil.process_iter(attrs=["pid", "name"]):
    if proc.info["name"] in ["chromedriver", "chrome"]:
        try:
            proc.kill()
            print(f"Processo encerrado: {proc.info['name']} (PID {proc.info['pid']})")
        except psutil.NoSuchProcess:
            print(f"Processo {proc.info['name']} (PID {proc.info['pid']}) não encontrado.")
        except Exception as e:
            print(f"Erro ao encerrar processo: {e}")

            
options = Options()
#options.add_argument("--disable-gpu")  # Desativa GPU para melhorar desempenho
options.add_argument("--no-sandbox")  # Evita problemas de permissão
options.add_argument("--disable-dev-shm-usage")  # Melhora estabilidade
options.add_argument("--blink-settings=imagesEnabled=false")  # Desativa imagens
options.add_argument("--disable-extensions")  # Desativa extensões
options.add_argument("--disable-popup-blocking")  # Evita bloqueios de pop-up
options.add_argument("--disable-infobars")  # Remove barra de informações do Chrome
options.add_argument("--headless")  # Modo headless (opcional)
service = Service(ChromeDriverManager().install())

data_hora0 = datetime.datetime.now(timezone)
data_hora00 = str(data_hora0)
print(f"Hora de início: {str(data_hora0)[0:16]}")

driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 300)
driver.get("https://plataformabrasil.saude.gov.br/login.jsf")
driver.maximize_window()

print("Abrindo Plataforma Brasil")
time.sleep(10)

while True:
    wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/div[3]/div/div/form[1]/input[4]')))
    driver.find_element(By.XPATH,'//*[@id="j_id19:email"]').clear() # email
    driver.find_element(By.XPATH,'//*[@id="j_id19:email"]').send_keys(login) # email
    driver.find_element(By.XPATH,'//*[@id="j_id19:senha"]').clear() # senha
    driver.find_element(By.XPATH,'//*[@id="j_id19:senha"]').send_keys(senha) # senha
    
    driver.find_element(By.XPATH, '//*[@id="j_id19"]/input[4]').click() # logar"
    time.sleep(2)
    
    try:   
        driver.find_element(By.XPATH, 
                            '//*[@id="formModalMsgUsuarioLogado:idBotaoInvalidarUsuarioLogado"]').click()
    except:
        pass 
        
    try:
        valid_login = driver.find_element(By.XPATH,"/html/body/div[2]/div/div[4]/div").text
        #print(valid_login)
        if "sessão" in valid_login:
            break
    except:
        continue

print("Login realizado com sucesso")

time.sleep(10)

list_CAAE = []
soup = BeautifulSoup(driver.page_source, 'html.parser')
paginas0 = soup.find("table",class_="rich-dtascroller-table").text
paginas0 = re.search((r'de (.*?) registro\(s\)'), paginas0).group(1)
paginas = int((int(paginas0)-1)/10)

for i in range(paginas+1):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    try:
        time.sleep(10)
        wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/div[6]/div[1]/form/div[3]/div[2]/table/tfoot/tr/td/div/table/tbody/tr/td[6]'))).click() #clicar no >>
    except:
        pass
    
    a = []
    aa = soup.find_all("label")

    for label in aa:
        a.append(label.text)
    
    for item in a:
        if '5262' in item:
            list_CAAE.append(item)
            #print(item)

list_CAAE = set(list_CAAE)
list_CAAE = list(list_CAAE)
list_CAAE = [item.replace("\n", "") if isinstance(item, str) else item for item in list_CAAE]
print(f"CAAEs válidos extraídos: {len(list_CAAE)}")

CAAE = list_CAAE

df_email = []
df_CAAE = []
count = 0

for i in CAAE:

    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        try:
            t1 = datetime.datetime.now(timezone)

            driver.find_element(By.XPATH,'/html/body/div[2]/div/div[6]/div[1]/form/div[2]/div[2]/table[1]/tbody/tr/td[2]/table/tbody/tr[2]/td/input').clear() #apagar
            driver.find_element(By.XPATH,'/html/body/div[2]/div/div[6]/div[1]/form/div[2]/div[2]/table[1]/tbody/tr/td[2]/table/tbody/tr[2]/td/input').send_keys(i) #escrever CAAE
            driver.find_element(By.XPATH,'/html/body/div[2]/div/div[6]/div[1]/form/div[2]/div[2]/table[1]/tbody/tr/td[2]/table/tbody/tr[2]/td/input').send_keys('\ue006') #clicar para pesquisar

            o = 0
            while o < 10:
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/div[6]/div[1]/form/div[3]/div[2]/table/tbody/tr/td[10]/a/img'))).click() #clicar na lupa
                    break
                except:
                    # Esperar 1 segundo antes de tentar novamente
                    time.sleep(1)
                    o += 1

            time.sleep(5)

            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/div[3]/div[2]/form/a[2]'))).click() #voltar ao menu
                        
            #extrai o nome do estudo
            nome_estudo = soup.find('td', class_="text-top").text[21:].replace('"',"") 
                        
            #extrai o PI
            PI = soup.find_all("td")[6].text 
            PI = PI.replace("\n", "")

            #extrai o primeiro histórico de trâmites
            a = soup.find(id='formDetalharProjeto:tableTramiteApreciacaoProjeto:tb') 
            time.sleep(2)
            a = a.find_all('span')
            b = []
            for span in a:
                b.append(span.text)

            q = []
            output = []
            x = 0

            while x < len(b[0::8]):
                t = f"""
                    <tr>
                    <th>{x+1}</th> 
                    <td>{b[0::8][x]}</td> 
                    <td>{b[1::8][x]}</td> 
                    <td>{b[2::8][x]}</td> 
                    <td>{b[3::8][x]}</td> 
                    <td>{b[4::8][x]}</td> 
                    <td>{b[5::8][x]}</td> 
                    <td>{b[6::8][x]}</td> 
                    <td>{b[7::8][x]}</td>
                    </tr>
                    """
                q.append(t)
                x = (x + 1)
                
            output = ''.join(q)

            CAAE_estudo = soup.find_all("td")[15].text
            CAAE_estudo = CAAE_estudo.replace("\n", "")
            CAAE_estudo = CAAE_estudo.replace("CAAE: ","")

            tabela_tramites = f"""
                            <table border="1" class="dataframe" style="text-align: center"> 
                            <thead><tr> 
                            <th></th> 
                            <th>Apreciação</th> 
                            <th>Data/Hora</th> 
                            <th>Tipo Trâmite</th> 
                            <th>Versão</th> 
                            <th>Perfil</th> 
                            <th>Origem</th> 
                            <th>Destino</th> 
                            <th>Informações</th> 
                            </tr></thead> 
                            <tbody>{output}</tbody> 
                            </table>
                            """

            corpo_email =   f"""
                            <p><b>{nome_estudo}</b></p> 
                            <p>CAAE: {CAAE_estudo}</p> 
                            <p>{PI}</p> 
                            {tabela_tramites}
                            """

            df_email.append(corpo_email)
            df_CAAE.append(CAAE_estudo)
            
            t2 = datetime.datetime.now(timezone)
            t = t2-t1

            #Contador
            count = count + 1
            con = f'Progresso: {count}/{len(CAAE)} Duração: {str(t)[2:9]}'
            print(con)

            break

        except Exception as e:
            retry_count += 1
            print(f"Erro no CAAE {i}: {e}. Tentativa {retry_count} de {max_retries}")
            # Recarregar página ou voltar à página inicial
            wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/div[3]/div[2]/form/a[2]'))).click() #voltar ao menu
            time.sleep(10)

print("Trâmites extraidos")

driver.close()

# Substituir "Hoje"
os.replace("new.csv", "old.csv")

# Criar DataFrame com as informações de estudo, CAAE e tabela do histórico de tramites
new = pd.DataFrame(zip(df_CAAE, df_email), columns=['CAAE', "email"]).sort_values(by=['CAAE'])

# Criar o CSV para salvar para comparar 
new.to_csv("new.csv", index=False)

# Comparar os resultados
old = pd.read_csv("old.csv")
comparar = pd.merge(
    new, 
    old, 
    on = 'CAAE', 
    how = 'outer',
    )
comparar = comparar[comparar["email_x"] != comparar["email_y"]]

# Monta lista com os email
join1 = comparar['email_x'].tolist()

vezes = len(join1)

join1 = '<br/>'.join(join1)
print(join1)

# Config do email
data = datetime.date.today().strftime('%d/%m/%Y')
data_hora = datetime.datetime.now(timezone) 
data_hora = data_hora.strftime("%d/%m/%Y %H:%M:%S")

print("configurando email")


def enviar_email():
    
    data_hora1 = datetime.datetime.now(timezone)
    str_data_hora1 = data_hora1.strftime("%d/%m/%Y %H:%M:%S")
    tempo = (data_hora1 - data_hora0)
    
    corpo_email = f"""
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> 
    <p>Bom dia equipe,</p> 
    <p>Abaixo os estudos que tiveram atualizações na Plataforma Brasil no dia {data}.</p> 
    <p>Houve atualização em <b>{vezes}</b> estudos.</p> 
    <br/> 
    {join1}
    <br/> 
    <p>Um ótimo dia a todos e todas!</p>
    """

    msg = email.message.Message()
    msg['Subject'] = f'Últimas atualizações da PB de {data_hora}'
    msg['From'] = 'regulatorios.aids@gmail.com'
    msg['To'] = destinatário
    password = 'hwle abms newc pubc' 
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(corpo_email)

    s = smtplib.SMTP('smtp.gmail.com: 587')
    s.starttls()
        
    # Login Credentials for sending the mail
    s.login(msg['From'], password)
    s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('utf-8'))

# Enviar email e registrar o término do programa

data_hora1 = datetime.datetime.now(timezone)
data_hora_str = data_hora1.strftime("%d/%m/%Y %H:%M:%S")
tempo = (data_hora1 - data_hora0)
tempo_str = str(tempo)

if vezes > 0:
    data_hora_str = data_hora0.strftime("%d/%m/%Y %H:%M:%S")
    file = open("registro.txt", "a")
    file.write(f'\n\n{data_hora00} - O programa comecou a rodar. \n')
    file.write(f'{data_hora_str} - O email foi enviado com sucesso. {vezes} estudos atualizados. Demorou: {tempo} minutos')
    file.close()
    enviar_email()
    print(f"Email enviado. Hora de término: {data_hora_str[0:16]}. Duração: {tempo_str[0:16]}")
    
else:
    data_hora_str = data_hora0.strftime("%d/%m/%Y %H:%M:%S")
    file = open("registro.txt", "a")
    file.write(f'\n\n{data_hora00} - O programa comecou a rodar. \n')
    file.write(f'{data_hora_str} - O email nao precisou ser enviado. {vezes} estudos atualizados. Demorou: {tempo} minutos')
    file.close()
    print(f"Não foi necessário enviar email. Hora de término: {data_hora_str[0:16]}. Duração: {tempo_str[0:16]}")
