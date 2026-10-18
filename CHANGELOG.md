# Changelog

All notable changes to this repository are listed here.
Versions follow [Semantic Versioning](https://semver.org/); while the toolkit is below 1.0, interfaces may still change between minor versions.
Versions 0.1.0–0.1.2 were numbered retroactively on 2026-10-18 from the commit history.

## [0.2.0] - 2026-10-18

### Added
- Project page at `docs/index.html` (GitHub Pages, served from `/docs`).
- Videos of the two IUS 2026 poster samples: wire phantom wavelength tagging (Fig. 2) and ex vivo porcine heart RF ablation monitoring (Fig. 3), in `docs/media/`.
- `tools/media/build_poster_videos.py`: rebuilds both videos from the lab data and writes `docs/media/manifest.json` with input and output SHA-256 hashes, the toolkit commit, and the figures quoted on the page.
- `tools/media/build_site_images.py`: web-size system figure and link-preview card.
- Square (1080x1080) cuts of both videos for social posts in `docs/media/social/`.
- This changelog.

### Changed
- README retitled to OPERA, with links to the project page and videos.

## [0.1.2] - 2026-05-15

### Fixed
- Local issues across the TCP server, shared memory, and path bootstrap (`setup_paths`).

## [0.1.1] - 2026-04-16

### Added
- TCP server and package assembly.
- Citation template for the arXiv preprint (arXiv:2604.15255).

## [0.1.0] - 2026-04-11

### Added
- First public skeleton: Arduino trigger monitor, Verasonics host template, shared-memory backend, configuration templates, mock dataset, system figure, notices and credits.

[0.2.0]: https://github.com/RyoMurakami-MedRobo/OPERA_Realtime-Multiwavelength-PA-Toolkit/compare/861fe76...v0.2.0
[0.1.2]: https://github.com/RyoMurakami-MedRobo/OPERA_Realtime-Multiwavelength-PA-Toolkit/compare/3aa8bd5...861fe76
[0.1.1]: https://github.com/RyoMurakami-MedRobo/OPERA_Realtime-Multiwavelength-PA-Toolkit/compare/de9be05...3aa8bd5
[0.1.0]: https://github.com/RyoMurakami-MedRobo/OPERA_Realtime-Multiwavelength-PA-Toolkit/tree/de9be05
