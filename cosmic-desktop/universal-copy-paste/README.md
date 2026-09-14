# Fedora COSMIC — Super clipboard v2

Deze versie bevat de keyd-oplossing uit het gesprek, met globale Super+A/C/V/X en terminaluitzonderingen voor COSMIC Terminal, Kitty, Foot en Alacritty. Voor reguliere Fedora met DNF en een COSMIC Wayland-sessie; niet voor Fedora Atomic/OSTree.

## Installeren

Pak de ZIP uit en open een terminal in de uitgepakte map. Lees het script en voer het als je gewone desktopgebruiker uit:

```bash
bash install-keyd-super-clipboard.sh
```

Start niet met `sudo`: het script bepaalt gebruikersnaam via `id` en home via `getent passwd`, en gebruikt zelf sudo voor systeembestanden en pakketbeheer. DNF vraagt bevestiging voor COPR/pakketten. Internet is nodig.

Het script voert `sudo dnf copr enable alternateved/keyd` en `sudo dnf install keyd curl python3` uit. Daarna schrijft het onderstaande bestanden, voegt de gebruiker met `usermod -aG keyd` toe aan de keyd-groep en activeert `keyd.service` met `enable --now`; een restart laadt de nieuwe configuratie.

**Log daarna volledig uit en opnieuw in, of reboot.** De bestaande sessie en systemd user manager kunnen nog oude groepsrechten hebben. Alleen een nieuwe terminal openen is niet altijd voldoende. Een geslaagde servicestart bewijst op zichzelf nog niet dat de app-mappings werken.

## Globale configuratie: `/etc/keyd/default.conf`

```ini
[ids]
*

[meta]
a = C-a
c = C-insert
v = S-insert
x = C-x
```

`meta` is de Super-laag. Super+A geeft Ctrl+A, Super+C geeft Ctrl+Insert, Super+V geeft Shift+Insert en Super+X geeft Ctrl+X. Dit geldt voor alle matchende toetsenborden. Ondersteuning van Ctrl+Insert/Shift+Insert hangt van de applicatie af.

## Terminalconfiguratie: `~/.config/keyd/app.conf`

```ini
[com-system76-cosmicterm]
super.c = C-S-c
super.v = C-S-v

[kitty]
super.c = C-S-c
super.v = C-S-v

[foot]
super.c = C-S-c
super.v = C-S-v

[alacritty]
super.c = C-S-c
super.v = C-S-v
```

COSMIC Terminal kan bij Ctrl+Insert anders letterlijk `5~` typen in plaats van kopiëren, zoals in het eerdere gesprek. De application mapper gebruikt daarom voor deze terminals Ctrl+Shift+C/V. Laat deze standaard terminalbindings ingeschakeld. Super+A/X blijven de globale Ctrl+A/X; in een shell zijn dit shellcommando's, niet noodzakelijk selecteren/knippen.

## Workaround voor de COSMIC application mapper van keyd v2.6.0

De besproken v2.6.0-versie had een COSMIC application mapper-probleem. Het script back-upt de geïnstalleerde `/usr/bin/keyd-application-mapper` als `/usr/bin/keyd-application-mapper.bak-DATUM-TIJD-PID` en installeert de actuele mapper van upstream master:

https://raw.githubusercontent.com/rvaiya/keyd/master/scripts/keyd-application-mapper

Het downloadt via HTTPS naar een tijdelijke map en controleert Python-syntaxis en aanwezigheid van COSMIC-code vóór vervanging. Er wordt geen download direct door een shell uitgevoerd. Bron-URL en SHA-256 worden bij de backups opgeslagen. De syntaxiscontrole is geen garantie van compatibiliteit: master kan later wijzigen. De workaround wordt bij elke uitvoering toegepast, ook wanneer het pakket inmiddels nieuwer is. Pakketupdates kunnen dit bestand opnieuw vervangen; controleer bij terugkeer van het probleem de pakketversie en mapper. De daemon zelf blijft uit COPR komen.

## Automatisch starten

`~/.config/systemd/user/keyd-application-mapper.service`:

```ini
[Unit]
Description=keyd application mapper
After=graphical-session.target

[Service]
ExecStart=/usr/bin/keyd-application-mapper
Restart=on-failure

[Install]
WantedBy=default.target
```

Het script importeert de huidige Wayland/desktop-omgeving in de user manager en voert uit:

```bash
systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_RUNTIME_DIR
systemctl --user restart keyd-application-mapper.service
```

Bij een bestaande service volgt ook een restart. `After` bepaalt alleen volgorde; het start graphical-session.target niet zelf. Bij ontbrekende sessievariabelen na een volgende login kun je vanuit COSMIC Terminal uitvoeren:

```bash
systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_RUNTIME_DIR
systemctl --user restart keyd-application-mapper.service
```

## Backups en herstel

Elke uitvoering maakt een unieke backupmap onder `~/.local/state/keyd-super-clipboard/backups/DATUM-TIJD-PID/`. Daarin staan een kopie van de bestaande `/etc/keyd`-directory, de bestaande app.conf en user-service indien aanwezig, en de downloadgegevens. De globale backup behoudt root-eigenaarschap; lezen/herstellen kan sudo vereisen. De oude mapper staat naast het originele systeembestand; het precieze pad staat in `mapper-backup-path.txt`.

Bestaande default.conf, app.conf en de genoemde service worden na backup vervangen, niet samengevoegd. Andere globale keyd-configs blijven staan en kunnen nog met deze configuratie conflicteren. Bestaande user-service drop-ins blijven eveneens actief. Vergelijk bij eigen mappings eerst de backups. Fouten stoppen het script; er is geen automatische rollback van reeds uitgevoerde stappen.

Herstel: stop de mapper met `systemctl --user disable --now keyd-application-mapper.service`, kopieer de gewenste oude bestanden vanuit de aangegeven backup terug naar hun oorspronkelijke paden (sudo voor `/etc/keyd` en `/usr/bin`), en voer `sudo systemctl restart keyd.service` en `systemctl --user daemon-reload` uit. Start een herstelde mapper-service alleen als je die opnieuw wilt gebruiken. Ontbrak een bestand vóór installatie, verwijder dan alleen het door dit script aangemaakte bestand. COPR/pakketten en het nieuwe groepslidmaatschap worden hiermee niet automatisch teruggedraaid.

## Controleren en problemen oplossen

Na opnieuw inloggen:

```bash
id -nG
systemctl status keyd.service --no-pager
systemctl --user status keyd-application-mapper.service --no-pager
journalctl --user -u keyd-application-mapper.service -b --no-pager -n 60
sudo journalctl -u keyd.service -b --no-pager -n 60
```

De groepenlijst moet `keyd` bevatten. Test Super+A/C/V/X in een teksteditor en Super+C/V met geselecteerde tekst in COSMIC Terminal. Wissel eerst van venster zodat de mapper de actieve app detecteert. Verschijnt `5~`, controleer mapperstatus, groepsrechten, app-id en terminalbindings. Aanvullende mapperinformatie kan in `~/.config/keyd/app.log` staan. Stop een eventueel handmatig gestarte mapper voordat je de service gebruikt.

Het aanbevolen pad gebruikt uitsluitend keyd en de application mapper. Schakel eerder aangemaakte conflicterende COSMIC custom shortcuts voor Super+A/C/V/X uit. ydotool is niet nodig; het script verwijdert geen bestaande tools of desktopinstellingen.

## Bronnen en verificatie

- Upstream keyd en Fedora-installatieverwijzing: https://github.com/rvaiya/keyd
- COPR: https://copr.fedorainfracloud.org/coprs/alternateved/keyd/
- Actuele mapper: https://github.com/rvaiya/keyd/blob/master/scripts/keyd-application-mapper
- COSMIC mapper-problemen: https://github.com/rvaiya/keyd/pull/1261

Pakket samengesteld op 14 september 2026. Bash-syntaxis en ZIP-integriteit zijn gecontroleerd. De installatie is bij het maken van deze ZIP niet uitgevoerd; functionele werking moet op je Fedora COSMIC-sessie worden getest.
