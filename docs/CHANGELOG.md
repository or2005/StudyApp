# Changelog

## [4.5.3] - 2026-09-03

### Fixed
- Hebrew no longer appears reversed on English Windows
- In-app update retries the ZIP if the setup file is missing, and hides a stale "update" after you are already current

## [4.5.2] - 2026-09-03

### Added
- Student health scanner in Settings: finds simple problems, repairs what it can, and says what to do
- Safe-room lock after 3 wrong passwords, with a security notice to the developer

## [4.5.1] - 2026-09-03

### Added
- Settings screen: check for updates, install now, install from a file, and auto-check toggle

## [4.5.0] - 2026-09-03

### Added
- In-app toasts for level-up and daily goal, without a Windows dialog
- Window title follows the current screen (home, subject, practice, results)
- Home greeting hero, subject tiles, and a one-time tip on the next-action button
- Practice feedback card that scrolls into view after an answer
- Fresh teal app icon (open book and spark)

### Updated
- Onboarding, lessons, results, and empty mistakes state to a tighter studio finish
- Buttons darken on press so clicks feel physical

## [4.4.0] - 2026-09-02

### Updated
- Smoother scrolling and screen transitions (no CustomTkinter canvas redraw on every wheel tick)
- Next in-app update installs this smoothness automatically when auto-check is on

## [4.3.0] - 2026-09-02

### Added
- In-app software updates: check on launch, manual check, download from the internet, or install from a local setup/zip file
- Optional anonymous ping (off by default): version, OS, and a random install id only, never name, age, Israeli ID, or learning data

### Updated
- Settings, About, and dashboard banner for a pending newer version
- Privacy wording in the terms

## [4.2.0] - 2026-09-02

### Added
- Linux support for common distros (Ubuntu, Debian, Fedora, Arch, openSUSE, Alpine, …)
- Portable Linux download (`StudyApp.sh` + Tkinter hints per distro)
- User install script and `.desktop` launcher
- GitHub Actions packages for Windows and Linux
- Cross-platform single-instance lock, fonts, window icon, and TTS

### Updated
- Public downloads documented for Windows 10, Windows 11, and Linux

## [4.1.0] - 2026-09-02

### Added
- Public Windows build: `StudyApp.exe` folder + ZIP, no Python required
- App icon and Windows file version
- Expanded original lesson and question banks (beginner / intermediate / advanced)
- Meimad sitting, general exam, daily review, and question reports (desktop)

### Updated
- Hebrew-first desktop app is the only product surface
- Release docs and user readme for install-from-zip

### Fixed
- Installer script now uses the full spec (data files, icon, version)

## [0.1.0] - 2026-09-01

### Added
- Hebrew-first learning dashboard
- diagnostic onboarding flow
- subject-based lesson and practice screen
- adaptive daily plan generation
- weak-topic prioritization
- focus and mood-aware learning suggestions
- rewards, streaks, and points system
- local persistence for student profile and progress
- dark, calm desktop UI
- project documentation and lightweight terms template
