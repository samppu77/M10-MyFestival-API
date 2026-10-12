# My Festival REST API – M10 endpoint-dokumentti

**Tekijä:** [Kirjoita oma nimi]  
**Julkinen osoite:** `https://[RAHTI-OSOITE]`  
**GitHub:** `https://github.com/[KÄYTTÄJÄ]/[REPO]`  
**Tarkistimen tulos:** [Lisää oikea tulos ajettuasi tarkistimen Rahti-osoitteeseen, esim. 20/20]

> **Ennen palautusta:** Korvaa hakasulkujen paikat, kopioi esimerkkivastaukset omasta julkaistusta APIsta ja liitä tarkistimen koko tuloste. Alla olevat GET-esimerkit perustuvat tässä paketissa olevaan tietokantaan.

## 1. Endpointit

| Metodi | Polku | Onnistuminen | Virhe |
|---|---|---|---|
| GET | `/api/artists` | 200 ja lista artisteista | – |
| GET | `/api/days` | 200 ja festivaalipäivät | – |
| GET | `/api/stages` | 200 ja lavat | – |
| GET | `/api/artists/{id}/events` | 200 ja esiintymiset | 404, artistia ei löydy |
| GET | `/api/timetable?day=YYYY-MM-DD` | 200 ja aikataulu | 400, väärä päivämuoto |
| POST | `/api/events` | 201 ja uusi `event_id` | 400, virheellinen syöte |
| DELETE | `/api/events/{id}` | 204, tyhjä vastaus | 404, tapahtumaa ei löydy |

## 2. Esimerkkikutsut ja vastaukset

**GET `/api/artists`**  
Kutsu: `curl.exe https://[RAHTI-OSOITE]/api/artists`  
Esimerkki listan yhdestä rivistä: `[{"artist_id":1,"name":"Aamuyön Valot","country":"FI"}, ...]` (lyhennetty listasta).

**GET `/api/days`**  
Kutsu: `curl.exe https://[RAHTI-OSOITE]/api/days`  
Vastaus: `[{"day_id":1,"date":"2027-07-16"},{"day_id":2,"date":"2027-07-17"}]`.

**GET `/api/stages`**  
Kutsu: `curl.exe https://[RAHTI-OSOITE]/api/stages`  
Esimerkki: `[{"stage_id":1,"name":"Aurinkolava"}, ...]` (lyhennetty listasta).

**GET `/api/artists/1/events`**  
Kutsu: `curl.exe https://[RAHTI-OSOITE]/api/artists/1/events`  
Vastaus: `[{"event_id":1,"day":"2027-07-16","stage":"Aurinkolava","starts":"14:00:00"}]`.  
Tuntematon artisti `/api/artists/999999/events`: **404**, `{"error":"Artistia ei loytynyt"}`.

**GET `/api/timetable?day=2027-07-16`**  
Kutsu: `curl.exe "https://[RAHTI-OSOITE]/api/timetable?day=2027-07-16"`  
Ensimmäinen rivi: `{"date":"2027-07-16","stage":"Aurinkolava","artist":"Aamuyön Valot","starts":"10:00:00","ends":"10:20:00"}`.  
Virheellinen päivä `?day=not-a-date`: **400** ja JSON-virheilmoitus.

**POST `/api/events`**  
Kutsu (PowerShell, yhden rivin komento):

```powershell
curl.exe -X POST "https://[RAHTI-OSOITE]/api/events" -H "Content-Type: application/json" -d '{"artist_id":1,"stage_id":1,"day_id":1,"start_dt":"2027-07-16 03:12:34"}'
```

**Odotettu vastauksen rakenne** (201, `event_id` vaihtelee):

```json
{"event_id": 19, "artist_id": 1, "stage_id": 1, "day_id": 1, "start_dt": "2027-07-16 03:12:34", "end_dt": "2027-07-16 03:57:34", "duration_min": 45}
```

Puuttuva kenttä tai olematon `artist_id`: **400** ja JSON-virheilmoitus. Vaihda yllä oleva oletettu `event_id` oikean POST-vastauksen tunnisteeseen ennen palautusta. Jos PowerShell käsittelee JSON-lainausmerkit väärin, testaa POST opettajan `test_endpoints.py`-tarkistimella.

**DELETE `/api/events/{id}`**  
Kutsu: `curl.exe -X DELETE https://[RAHTI-OSOITE]/api/events/[UUSI-EVENT-ID]`  
Olemassa oleva tapahtuma: **204**, ei JSON-runkoa. Sama DELETE uudelleen: **404** ja JSON-virheilmoitus. Älä poista olemassa olevia harjoitusdatan tapahtumia: käytä vain itse lisäämääsi testitapahtumaa.

## 3. Julkaisu Rahtiin

[Kirjoita julkaisun jälkeen omin sanoin 3–6 lausetta. Kuvaile, miten Rahti haki GitHubista lähdekoodin, rakensi Dockerfilellä imagen, käynnisti Deploymentin ja julkaisi HTTPS-osoitteen Routen kautta. Kerro myös yksi **oikeasti kohtaamasi** ongelma ja miten selvitit sen.]

## 4. Tietoturva

SQL-kyselyissä käyttäjän antamat arvot annetaan parametreina (`?`), joten syöte ei pääse muuttamaan SQL-lauseen rakennetta. POST-pyynnössä tarkistetaan pakolliset kentät, tunnisteet ja päivämäärän muoto sekä otetaan käyttöön SQLite-viiteavaintarkistukset. Tuotantokäytössä rajapinta tarvitsisi lisäksi käyttäjien tunnistautumisen, kirjoitusoikeuksien hallinnan ja pyyntöjen määrän rajoittamisen, sillä nykyiset POST- ja DELETE-reitit ovat avoimia.
