<p align="center"><img src="custom_components/heatzy_local/brand/icon@2x.png" width="150" alt="Heatzy Local logo"></p>
<h1 align="center">Heatzy Local</h1>
<p align="center">Local control for Wi-Fi-configured Heatzy Onyx radiators.</p>
<p align="center">
<img alt="Version" src="https://img.shields.io/badge/version-1.0.2-156A73">
<img alt="License" src="https://img.shields.io/badge/license-MIT-blue">
<img alt="Home Assistant" src="https://img.shields.io/badge/Home_Assistant-2026.10.1%2B-41BDF5">
<img alt="Protocol" src="https://img.shields.io/badge/control-local_LAN-F47735">
</p>
<p align="center"><a href="README.fr.md">Français</a> · <a href="docs/README.md">Documentation</a> · <a href="CHANGELOG.md">Changelog</a> · <a href="https://github.com/lugio/heatzy-local/releases/latest">Releases</a></p>

## Before you start

**Connect the radiator to your Wi-Fi first.** This integration does not provision its network connection. The current setup method uses the Heatzy app; see the [Wi-Fi and Home Assistant setup guide](docs/pairing.md). App-free Wi-Fi onboarding is being researched, not claimed as a supported feature.

Once Wi-Fi is configured, operation is local: no Gizwits account, cloud token or external Python dependency is required by this integration. This is an independent community project, not an official Heatzy integration.

## Install

Home Assistant **2026.10.1** is the tested version and declared minimum. Only **Heatzy Onyx**, product key `bb10d064f8de409db633b750faa22a52`, has been tested.

### HACS custom repository

1. Open HACS → Custom repositories.
2. Add `https://github.com/lugio/heatzy-local` as **Integration**.
3. Download Heatzy (local), then restart Home Assistant.
4. Open Settings → Devices & services → Add integration → **Heatzy (local)**.
5. Enter the radiator's LAN IP address.

This custom-repository installation does not imply inclusion in the default HACS catalogue.

### Manual installation

Download the ZIP from [Releases](https://github.com/lugio/heatzy-local/releases/latest), verify its SHA256, and extract `heatzy_local/` into `config/custom_components/`. Restart Home Assistant and add the integration using the radiator's IP address.

## Features

| Feature | Available behaviour |
|---|---|
| Local heating control | Comfort, eco, frost protection and off; HEAT preserves an already active preset |
| Adjustable setpoints | Comfort and eco numbers, read from the device |
| Internal temperature | Reported radiator temperature, not a calibrated room measurement |
| Weekly schedule | Seven days, 48 half-hour slots per day, local read/write action |
| Reported clock | Day/hour/minute and manual synchronization; freshness is not guaranteed |
| Override modes | Off, programme, holiday and automatic; no proven occupancy state |
| Verified writes | Serialized access, private backup, delay and readback verification |
| Local branding | Icons shipped with the integration, without an external image dependency |

## Important limits

- `power_data` is **not a validated consumption sensor**. Its physical meaning and unit are unresolved; it is a disabled-by-default diagnostic with no unit or device class. Use a separate electricity meter for watts and kWh.
- Reported clock fields can lag. Do not assume that every clock read is a fresh RTC measurement.
- The scheduled slot and the effective heating mode are separate. Not every unexpected preset change has been explained.
- Firmware representation bounds are not a guarantee that all setpoints are accepted. The official app's UI uses 7–30°C; extreme settings have not been tested.
- Short hardware checks do not establish long-term reliability. Wi-Fi quality and device firmware remain relevant.
- Other Heatzy models, app-free Wi-Fi provisioning and a real occupancy binary sensor are not validated.

See the [French user guide](README.fr.md) for actions, entity details, scheduling, clock synchronization and automation examples.

## Documentation and development

[Documentation index](docs/README.md) · [LAN protocol](docs/protocol.md) · [Setup and pairing](docs/pairing.md) · [Contribution guide](CONTRIBUTING.md) · [Security](SECURITY.md)

Run the offline regression suite:

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions runs the unit tests, Hassfest and HACS validation. A workflow badge or test result does not certify every device function.

## Update or remove

Back up `custom_components/heatzy_local/`, replace it with the release contents, and restart HA. Existing entity identifiers are retained by this release.

To remove it, delete its integration entries in HA, remove the directory, then restart HA. Private backups in `config/heatzy_local_backups/` are not automatically removed.

## License and acknowledgements

[MIT](LICENSE). Thanks to [Gizwits' reference source](https://github.com/gizwits/Gizwits-GAgent), [ha-jebao-pumps](https://github.com/markosharknz1/ha-jebao-pumps), and the community integrations used for comparison. Their behaviour on other products is not treated as proof of Onyx compatibility.
