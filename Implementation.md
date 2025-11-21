## Faza 1: Dwie VM

### 1. Tworzymy plik \*sh.

Zawartość:

```bash
sudo apt install -y telnet

sudo apt install -y nginx

sudo systemctl enable nginx

sudo chmod -R 755 /var/www/html

HOSTNAME=\$(hostname)

sudo echo \"\<!DOCTYPE html\> \<html\> \<body
style=\'background-color:rgb(240, 128, 128);\'\> \<h1\> Project 5:
Logging, Monitoring and Incident Response System &#128568; \</h1\>
\<p\>\<strong\>VM Hostname:\</strong\> \$HOSTNAME\</p\>
\<p\>\<strong\>VM IP Address:\</strong\> \$(hostname -I)\</p\>
\<p\>\<strong\>Application Version:\</strong\> V1\</p\>
\</body\>\</html\>\" \| sudo tee /var/www/html/index.html
```

![img](images/image29.png)

### 2. Tworzymy "instance Template"

Compute Engine -\> Virtual Machines -\> Instance Templates -\> Create
Instance Template

- Name: instance-template-project5
- Location: Regional
- Region: Any
- Machine Configuration:

  - Series: E2
  - Machine Type: e2-micro

- Firewall

  - Allow HTTP Traffic

- Advanced Options

  - Automation:

    - Startup Script: Copy paste z `project5.sh`

![](images/image9.png)

![](images/image17.png)

![](images/image36.png)

![](images/image24.png)

### 3. Tworzymy VM używając  "instance Template"

Opcje: Compute Engine -\> Instance Templates -\>
instance-template-project5 -\> Create VM

Name: vm1-project5

![](images/image51.png)

Name: vm2-project5

Edytowałam w zakładce `starupscript` 
`body style=\'background-color:rgb(128, 128, 0);`
i został dodany `&#128054;`

![](images/image35.png)

Name: vm3-project5

![](images/image37.png)

![](images/image7.png)


## Faza 2: Instalacja Aplikacji Nginx

Nie potrzebna poniewaz byla w startup-script. Zostało zrobione tylko
poniżej na wszystkich VM.

`sudo apt-get update`

![](images/image40.png)

![](images/image39.png)

![](images/image23.png)

## Faza 3: Instalacja Ops Agent

To samo dla wszystkich VM:

```bash
curl -sSO
https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh

sudo bash add-google-cloud-ops-agent-repo.sh --also-install
```

![](images/image63.png)

### Sprawdzenie:

```bash
sudo systemctl status google-cloud-ops-agent
```

![](images/image46.png)

### Druga VM:

![](images/image48.png)

![](images/image22.png)

### Trzecia VM:

![](images/image16.png)

![](images/image13.png)

### Update w celu dodania dodatkowej metryki niestandardowej:

![](images/image41.png)

![](images/image18.png)

![](images/image59.png)

## Faza 4: Dodanie alertów

#### 1. Tworzymy Topic w PubSub o nazwie `alert-remediation-topic` i domyślnych ustawieniach.

![](images/image55.png)

#### 2. Tworzymy grupowy e-mail i dodajemy jako kanał powiadomień nasz nowy grupowy adres e-mail.

![](images/image11.png)

![](images/image26.png)

#### 3. Dodajemy kanał PubSub.

![](images/image32.png)

#### 4. Tworzymy Policy w Alertach

![](images/image65.png)

![](images/image20.png)

#### 5. Tworzymy wskaźnik oparty na logach (niestandardowa metryka)

![](images/image14.png)

#### 6. Łączymy się przez SSH do VM i testujemy wskaźnik.

![](images/image15.png)

![](images/image2.png)

#### 7. W trakcie uruchamiania i wykonywania dostajemy alert o wysokim CPU (Sukces! Nasz alert działa)

![](images/image27.png)

![](images/image28.png)

#### 8. Tworzymy kolejne Policy w Alertach dotyczące, tym razem, błędu `nginx`

![](images/image12.png)

![](images/image61.png)

#### 9. Testujemy czy wysyłanie alertów dotyczących niestandardowej metryki oraz wysokiej wartości wykorzystania CPU działa:

![](images/image3.png)

![](images/image10.png)

![](images/image34.png)

![](images/image50.png)

![](images/image45.png)

##### Incydent Nginx (Zamknięty):

- *Powód:* Ten alert został wywołany przez chwilowy wzrost liczby błędów (metryka nginx_error_count była \> 0). W następnej minucie nie było już błędów, więc metryka wróciła do normy (do 0).
- *Wniosek:* System zobaczył, że warunek alertu nie jest już spełniony (problem zniknął), więc automatycznie zamknął incydent.

##### Incydenty CPU (Otwarte):

- *Powód:* Ten alert został wywołany przez wysokie CPU (\> 80%). To uruchomiło naszą automatyzację (Cloud Function), która wyłączyła maszyny.
- *Wniosek:* Maszyny przestały wysyłać jakiekolwiek metryki.
  System nigdy nie zobaczył, że CPU \"wróciło do normy\" (poniżej 80%).
  Zamiast tego metryka po prostu zniknęła. System trzyma incydent otwarty, aby poinformować nas, że problem nie został rozwiązany \"naturalnie\", ale wymagał interwencji (wyłączenia maszyny).

![](images/image25.png)

![](images/image54.png)

![](images/image47.png)

![](images/image64.png)

#### 10. Tworzymy zbiór danych BigQuery oraz ujście (_Sink_) logów do nowo utworzonego zbioru.

![](images/image21.png)

![](images/image53.png)

![](images/image31.png)

#### 11. Wywołujemy tworzenie logów na obu maszynach aby przetestować czy logi zapisują się w zbiorze danych w BigQuery.

![](images/image58.png)

![](images/image8.png)

Wpisujemy zapytanie SQL do wyświetlenia z naszego zbioru danych logi typu _nginx_error_. Dostajemy w wyniku 40 logów (po 20 logów z dwóch VM - zgadza się).

![](images/image57.png)

## Faza 5.1 Tworzenie dodatkowego alertu niestandardowego request count.

Wychodzimy z założenia, że nasza aplikacja będzie jedynie do użytku wewnętrznego przez mały zespół czteroosobowy więc nie spodziewamy się na niej dużego ruchu. Zależy nam jednak na jej dostępności.  W tym celu, aby wiedzieć czy nasza aplikacja nie ma znacznie większego ruchu niż zazwyczaj skonfigurujemy alert, informujący nas o tym, że ilość requestów HTTP GET lub post jest większa niż 500 w przeciągu godziny.

Bardzo istotnym krokiem przed wykonaniem kolejnych jest instalacja Ops Agenta oraz konfiguracja w /etc/google-cloud-ops-agent/config.yaml odbiornik logów Nginxa. Ten etap został dokładnie opisany w _Fazie 3_.

Następnie w pierwszej kolejności  należy utworzyć log-based metrics typu Counter o nazwie `custom.googleapis.com/nginx/request_count` dla projektu _lvl-up-logging_.

![](images/image56.png)

Następnie dodano filtr, który załapie podstawowe żądania HTTP, np.

![](images/image42.png)

Po utworzeniu metryki należy przygotować politykę alertowania.

![](images/image30.png)

Tworząc politykę alertowania wybrano wcześniej stworzoną metrykę opartą o logi.

![](images/image4.png)

Następnie ustawiamy wartości _Rolling window time_ na **1 hr** oraz _rollling window_ na **sum**. Rolling window time określa, ile minut/danych jest branych pod uwagę, a rolling window function mówi, jak te dane mają być połączone lub przetworzone, by ustalić, czy warunek alertu jest spełniony.

![](images/image52.png)

_Condition typ threshold_ oznacza sprawdzanie przekroczenia
progu.

_Alert trigger any time series violates_: alert pojawia się, gdy
choć jeden szereg czasowy przekracza próg.

_Threshold position above threshold_: progowa wartość jest
wartości graniczną, przekroczenie z góry aktywuje alert.

_Threshold value 500_: konkretny próg ustawiony na 500 requestów.

![](images/image43.png)

W kolejnym kroku zostały skonfigurowane notyfikacje drogą mailową oraz
do PubSub.
Dodatkowo określono standardową wartość czasu o którym incydent
 automatycznie się zamyka, poziom severity polityki oraz nazwę alertu --
[KURS GCP] - Wysoka ilość zapytań.

![](images/image33.png)

![](images/image44.png)

## Faza 5.2 Testowanie alertu request_count.

Aby zweryfikować czy alert działa wykorzystano skrypt w Python, który
wysyła 1000 zapytań na adres każdej z trzech maszyn.

`import requests`

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

urls = [
   "http://35.188.135.151/",
   "http://34.66.245.2/",
   "http://34.57.127.200/"
]

num_requests_per_url = 1000
max_workers = 20  # liczba jednoczesnych wątków

def send_request (url):
   try:
       response = requests.get(url, timeout=5)
       return url, response.status_code

   except Exception as e:
       return url, f"Error: {e}"

def main ():
   with ThreadPoolExecutor(max_workers=max_workers) as executor:
       futures = []

       for url in urls:
           futures += executor.submit(send_request, url) for _ in range(num_requests_per_url)

       for i, future in enumerate(as_completed(futures), 1):
           url, status = future.result()
           print(f"Request {i} to {url}: Status {status}")

if __name__ == "__main__":
   main()
```

Skutkowało to wywołaniem alertu, utworzeniem incydentu i wysłaniem
wiadomości email.

![](images/image19.png)

![](images/image38.png)

Oznacza to, że liczba żądań GET oraz POST w ciągu godziny wyniosła
więcej niż 500, jak przedstawia jeden z powyższych screenów. Metryka,
polityka oraz alertowanie zostały skonfigurowane i uruchomione poprawnie
i działają zgodnie z założeniami.

## Faza 6: Cloud Function

Tworzymy funkcję w Cloud Run Functions która będzie zatrzymywała VM
jeżeli Pub/Sub wyśle wiadomość o \>80% CPU.

1.  Włączamy następujące API:  cloudfunctions.googleapis.com \  
    cloudbuild.googleapis.com \   artifactregistry.googleapis.com
    stop-

2.  Tworzymy katalog w CLI "stop-vm-fn". W nim tworzymy plik
    main.py z funkcją która zatrzymuje VM po otrzymaniu wiadomości z
    Pub/Sub.
3.  ![](images/image6.png)
4.  2.2 W katalogu "stop-vm-fn" tworzymy plik requirements.txt
5.  ![](images/image1.png)
6.  2.3 Dodajemy uprawnienia IAM „Compute Instance Admin (v1)" do
    domyślnego konta usługi Compute Engine, aby funkcja mogła
    zatrzymywać maszyny wirtualne.
7.  ![](images/image62.png)
8.  2.4 Wdrażamy funkcję Cloud Function z bieżącego katalogu, ustawiamy
    entrypoint, trigger Pub/Sub i konto serwisowe.

![](images/image49.png)

## Faza 7: Testowanie systemu

1.  Łączymy się z VM przez SSH i instalujemy narzędzie stress

![](images/image5.png)

2.  Uruchamiamy test obciążenia

![](images/image60.png)

3.  Sprawdzamy CPU log - alert został otrzymany - sukces
4.  Sprawdzamy maila - mail otrzymany - sukces
5.  Sprawdzamy, czy VM została zatrzymana - sukces
