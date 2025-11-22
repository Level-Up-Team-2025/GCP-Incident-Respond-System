
 # Incident Response Plan
**Projekt:** GCP Production Monitoring System

**Właściciel Dokumentu:** Marta

**Zespół:** Eliza, Ewelina, Maria, Marta

**Data:** 22.11

---

## 1. Cel

Ten dokument opisuje procedury reagowania na incydenty wykryte przez nasz system monitoringu w Google Cloud Platform. Celem jest szybka identyfikacja, diagnoza i rozwiązanie problemów, aby zminimalizować ich wpływ na działanie aplikacji.

## 2. Role i Odpowiedzialność

| Rola | Osoba | Obowiązki |
| :--- | :--- | :--- |
| **Project Owner / Billing** | Maria | Zarządzanie dostępem (IAM), monitorowanie kosztów, ostateczna eskalacja. |
| **Developer / Coordinator** | Ewelina | Pierwsza linia reakcji (diagnoza), koordynacja działań naprawczych, komunikacja zespołu. |
| **Developer / Coordinator** | Marta | Weryfikacja, aktualizacja oraz utrzymanie  planu incydentu.|
| **System Design / Docs** | Eliza | Analiza przyczyn (Root Cause Analysis - RCA), przygotowanie post-mortem. |

## 3. Zdefiniowane Alerty i Poziomy Krytyczności

| Nazwa Alerty | Poziom Krytyczności | Opis | Kanał Powiadomień |
| :--- | :--- | :--- | :--- |
| `[KURS-GCP] Wysokie CPU na instancji` | **P2 (Wysoki)** | Użycie CPU na dowolnej instancji przekroczyło 80% przez ponad 1 minutę. Ryzyko spowolnienia lub awarii aplikacji. | `email_zespolu`, `PubSub_dla_Funkcji` |
| `[KURS-GCP] KRYTYCZNY BLAD NGINX!` | **P1 (Krytyczny)** | Wykryto co najmniej 1 nowy wpis w logu błędów Nginx (`error.log`). Aplikacja może nie działać poprawnie. | `email_zespolu` |
| `[KURS GCP] - Wysoka ilość zapytań` | **P1 (Krytyczny)** | Ilość zapytań wyslanych na adresy maszyn przekroczyła 500 wciągu godziny. Nieoczekiwane zwiększenie ruchu, możliwy atak DDoS. | `email_zespolu`|

## 4. Procedura Reagowania na Incydent (Krok po Kroku)

### Krok 1: Wykrycie i Powiadomienie (Automatyczne)
1. System (Cloud Monitoring) wykrywa anomalię (błąd Nginx, wysokie CPU lub ponadprzeciętną ilość zapytań).
2. System wysyła powiadomienie na zdefiniowane kanały (Email, Pub/Sub).
3. W przypadku alertu P2 (CPU): Uruchamiana jest automatyczna akcja (Cloud Function stop-vm-on-alert), która zatrzymuje maszynę.
4. W przypadku alertu P1 (Nginx): Wysyłany jest e-mail do zespołu jako sygnał o  potencjalnym incydencie wymagającym analizy.
5. W przypadku alertu P1 (Wysoka ilość zapytań): Wysyłany jest e-mail do zespołu jako sygnał o  potencjalnym incydencie pilnie wymagającym analizy.

### Krok 2: Potwierdzenie (Triage) - (Osoba: Ewelina)
1. Pierwsza dostępna osoba z zespołu (domyślnie Ewelina) widzi email i natychmiast potwierdza otrzymanie alertu (np. wysyłając "Zajmuję się tym" na grupowym czacie).
2. Czas reakcji (SLA): 1 godzina.
3. Ewelina loguje się do GCP, aby zweryfikować alert.
4. Dla Alertu Nginx:  Weryfikacja Logging -> Logs Explorer z zapytaniem logName:"nginx_error" aby zobaczyć treść błędu.
5. Dla Alertu Wysokiej ilości zapytań: Weryfikacja metryki w Monitoring → Metrics Explorer oraz analiza anomalii w ruchu. 


### Krok 3: Diagnoza i Rozwiązanie (Eskalacja) - (Eliza)
***Scenariusz 1:*** Alert CPU (P2)
1. Reakcja: Automatyczna (VM została zatrzymana).
2. Diagnoza (Po fakcie): Zespół analizuje, dlaczego doszło do przeciążenia. Weryfikacja Monitoring -> Dashboards -> VM Instances dla danych historycznych: czy był nagły wzrost, czy stały trend?
3. Rozwiązanie (Długoterminowe): Jeśli jest to stały trend, zmiana rozmiaru maszyny na większą, odpowiednio dostosowaną do aplikacji (np. e2-micro → e2-small). 

***Scenariusz 2:*** Alert Nginx (P1)

1. Diagnoza: Analiza blędu przy użyciu  Logs Explorer.
2. Diagnoza szczegółowa: Weryfikacja poprawnościkonfiguracji Nginx (sudo nginx -t) i błędy aplikacji.
3. Rozwiązanie: Naprawa błędów konfiguracyjnych (m.in. /etc/nginx/sites-available/default) i restart Nginxa (sudo systemctl reload nginx).
4. Eskalacja: Jeśli problem nie zostanie rozwiązany w 6 godzin, eskalacja do Marii. 

***Scenariusz 3:*** Alert Wysoka ilość zapytań (P1)

1. Diagnoza: Weryfikacja metryki zapytań i czy są przesłanki, wskazujące na to że może to być atak DDoS. Analiza: Weryfikacja czy ruch jest legalny (w logach Nginxa)
2. Rozwiązanie:  Dwie głownie możliwości: zastosowania reguł firewall / rate-limiting. Jeśli chodzi o ratę limiting, to można potencjalne w przyszłości rozbudować politykę alertowa tak, aby dostawać alerty jeśli duża ilość zapytań niż statystycznie za pewien okres czasu, np. godzinę przychodzi z powtarzalnych adresów IP. Alternatywne eskalacja do zespołu bezpieczeństwa.
3. Eskalacja: Jeśli nie możesz ograniczyć ruchu w 6 godzin, eskalacja do Marii.

### Krok 4: Post-Mortem (Po Incydencie) - (Osoba: Eliza)
1.  Po rozwiązaniu incydentu (nie później niż 24h po), **Eliza** organizuje krótkie spotkanie (15 min).
2.  Zespół odpowiada na pytania:
    * Co się stało?
    * Co poszło dobrze (np. automatyczne zatrzymanie VMki zadziałało)?
    * Co poszło źle (np. alert P1 nie był wystarczająco jasny)?
    * Jak możemy zapobiec temu w przyszłości? (np. "Zwiększamy typ maszyny na `e2-small`").
Bazując na odpowiedziach na te pytania **Eliza** przygotowuje i publikuje Root Cause Analysis oraz raport Post-Mortem.
3.  **Marta** aktualizuje plan incydentu.
