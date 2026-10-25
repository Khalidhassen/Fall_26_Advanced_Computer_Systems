# Environment and evidence provenance

## Inventory transcribed from my terminal output

The following was supplied in the project conversation. The original inventory text files were not present in the uploaded experiment ZIPs, so this document is a transcription, not a recovered raw log.

- Windows 11 Home, 10.0.26300, build 26300; native Windows collection, not WSL.
- Intel Core i7-12700H, 14 physical cores, 20 logical processors.
- 16 GiB RAM: two 8 GiB SK Hynix modules; reported speed/configured speed 3200.
- SSD DeviceId 0: NVMe Micron_2400_MTFDKBA1T0QFM; firmware V3MA003.
- Physical size: 1,024,203,640,320 bytes; Windows reported NVMe bus.
- C: NTFS volume: 996,750,462,976 bytes (approximately 928.3 GiB).
- Snapshot 2026-10-24T23:15:16.3926360-04:00: Healthy / OK; temperature 60°C; free bytes 17,970,708,480.
- Laptop reported plugged in. Performance plan GUID: 27fa6203-3987-4dcc-918d-748559d549ec.

## Evidence preserved in the repository

Every study includes fio version and power-plan records. Available per-trial state snapshots preserve free bytes, returned temperature, and local timestamps. Baseline space records are preserved separately. All archived power-plan records show Performance. Source archives and exact content hashes are listed under data/raw.

Every archived temperature sample returned 60°C. Constant readings do not prove a constant die temperature or absence of throttling. The inventory's TemperatureMax field was 0 and is unusable; Microsoft defines that field as the maximum operating temperature, not the observed session peak. Wear returned 0 but was not independently validated. Blank power-on-hour and uncorrected-error fields mean unavailable, not zero errors. Healthy / OK is the reported health status, not proof that every performance anomaly is harmless.

Negotiated PCIe speed/width, device-cache hit rates, internal firmware events, SLC occupancy, throttle flags, physical NAND locations, and whole-drive preconditioning were not measured. Micron describes the product family as PCIe Gen4 / NVMe 1.4; that is a manufacturer capability, not a measured active link.
