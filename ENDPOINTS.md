# M10 – My Festival REST API: endpoint-dokumentti

**Tekijä:** Samuel Sippola  
**GitHub:** https://github.com/samppu77/M10-MyFestival-API  
**Julkinen API:** https://festival-samuelsip-samuelsi.2.rahtiapp.fi  
**Tarkistin:** `test_endpoints.py` – **20/20 checks passed** (julkinen Rahti-osoite, 12.10.2026)

## 1. Rajapinnan endpointit ja esimerkit

Alla on esimerkkikutsut ja vastaukset. GET-listojen vastauksista esitetään tilan säästämiseksi vain yksi tai muutama rivi; varsinainen API palauttaa kaikki kyseiseen hakuun kuuluvat rivit.

**1. `GET /api/artists` – artistien hakeminen.**  
Kutsu: `GET https://festival-samuelsip-samuelsi.2.rahtiapp.fi/api/artists`  
Vastaus **200 OK**, esimerkiksi: `[ {"artist_id":1,"name":"Aamuyön Valot","country":"FI"} ]`

**2. `GET /api/days` – festivaalipäivät.**  
Kutsu: `GET https://festival-samuelsip-samuelsi.2.rahtiapp.fi/api/days`  
Vastaus **200 OK**: `[{"day_id":1,"date":"2027-07-16"},{"day_id":2,"date":"2027-07-17"}]`

**3. `GET /api/stages` – lavat.**  
Kutsu: `GET https://festival-samuelsip-samuelsi.2.rahtiapp.fi/api/stages`  
Vastaus **200 OK**, esimerkiksi: `[ {"stage_id":1,"name":"Aurinkolava"} ]`

**4. `GET /api/artists/{id}/events` – yhden artistin esiintymiset.**  
Kutsu: `GET https://festival-samuelsip-samuelsi.2.rahtiapp.fi/api/artists/1/events`  
Vastaus **200 OK**: `[{"event_id":1,"day":"2027-07-16","stage":"Aurinkolava","starts":"14:00:00"}]`  
Tuntematon artisti, esim. `/api/artists/999999/events`: **404 Not Found** ja `{"error":"Artistia ei loytynyt"}`.

**5. `GET /api/timetable?day=YYYY-MM-DD` – ohjelma aikajärjestyksessä.**  
Kutsu: `GET https://festival-samuelsip-samuelsi.2.rahtiapp.fi/api/timetable?day=2027-07-16`  
Vastaus **200 OK**, esimerkkirivi: `[ {"date":"2027-07-16","stage":"Aurinkolava","artist":"Aamuyön Valot","starts":"10:00:00","ends":"10:20:00"} ]`  
Ilman `day`-parametria palautuu koko ohjelma. Väärä muoto, esim. `day=not-a-date`: **400 Bad Request** ja JSON-virheviesti.

**6. `POST /api/events` – uuden esiintymisen lisääminen.**  
Kutsu: `POST https://festival-samuelsip-samuelsi.2.rahtiapp.fi/api/events`, otsake `Content-Type: application/json` ja JSON-runko:

```json
{"artist_id":1,"stage_id":1,"day_id":1,"start_dt":"2027-07-16 03:12:34"}
```

Vastaus **201 Created**, esimerkiksi:

```json
{"event_id":19,"artist_id":1,"stage_id":1,"day_id":1,"start_dt":"2027-07-16 03:12:34","end_dt":"2027-07-16 03:57:34","duration_min":45}
```

`event_id` on tietokannan luoma ja voi olla eri. Puuttuvat kentät, virheellinen aika tai viiteavaintunniste palauttavat **400 Bad Request** ja JSON-virheviestin.

**7. `DELETE /api/events/{id}` – esiintymisen poistaminen.**  
Kutsu: `DELETE https://festival-samuelsip-samuelsi.2.rahtiapp.fi/api/events/19` (käytä oman POST-testin palauttamaa tunnistetta).  
Onnistunut vastaus **204 No Content**, tyhjä runko. Tuntematon tai jo poistettu tunniste: **404 Not Found** ja `{"error":"Tapahtumaa ei loytynyt"}`.

## 2. Julkaisu CSC Rahtiin

Tein Flask-sovelluksen paikallisesti ja testasin sen SQLite-kantaani vastaan. Vein tiedostot julkiseen GitHub-repositorioon ja käytin Rahdissa toimintoa **Import from Git**, joka haki koodin ja rakensi Dockerfilellä kontti-imagen (**build**). Rahti käynnisti sovelluksen **deploymentin Podissa** portissa 8080 ja julkaisi sen **Service- ja Route-resurssien** kautta HTTPS-osoitteessa. Suojatussa Routessa on **TLS termination: Edge** sekä **Insecure traffic: Redirect**. Projektin luonnissa tuli aluksi virhe, koska CSC-projektinumero puuttui kuvauksesta; lisäsin `csc_project: 2021201`, minkä jälkeen projekti syntyi. Julkaistun APIn opettajan tarkistin läpäisi kaikki **20/20** tarkistusta.

## 3. Tietoturva ja rajoitukset

SQL-kyselyissä käyttäjän arvot välitetään parametreina (`?`), mikä ehkäisee SQL-injektioita. POST tarkistaa pakolliset kentät, tunnisteiden tyypit, aikamuodon ja SQLite-viiteavaimet; virheistä palautuu 400. HTTPS suojaa tiedonsiirtoa. Harjoitus-API:ssa ei ole tunnistautumista, joten kuka tahansa voi lähettää POST- ja DELETE-pyyntöjä: oikeaan käyttöön tarvittaisiin käyttöoikeudet ja pyyntöjen rajoittaminen. SQLite-tiedosto on pakattu kontti-imageen, joten käynnissä olevaan konttiin tehdyt muutokset eivät säily uuden Podin tai buildin jälkeen.
