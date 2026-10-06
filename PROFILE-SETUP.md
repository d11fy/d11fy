# Maintaining this profile

The profile combines an animated ASCII rendering of the account's current public avatar, a terminal information card, and real public GitHub contribution data. The initial calendar was fetched from GitHub, not generated from sample data.

## Daily updates

`.github/workflows/update-profile.yml` runs daily around 06:17 UTC (scheduled runs can be delayed), on relevant code changes, or manually from **Actions → Refresh profile contributions → Run workflow**. It uses the repository's built-in `GITHUB_TOKEN` through checkout credentials, with `contents: write`. No personal access token or secret needs to be added.

The update script uses Python's standard library. It validates dates and counts before replacing the previous calendar, so an incomplete GitHub response fails the job instead of publishing invented activity. The graph shows GitHub's publicly displayed activity, which depends on the account's visibility settings. Longest streak is measured within the displayed calendar.

If a workflow is blocked by account or organization policy, enable GitHub Actions and permit this workflow to write repository contents. If no run appears automatically, launch it manually in the Actions tab.

## Updating the photo or biography

The current avatar was converted to ASCII once. To use another photo, run `python scripts/make_profile_art.py /path/to/photo.png` after installing Pillow. The daily workflow does not download or alter your photo. Edit the information rows in that script to update the biography, then regenerate the artwork. Keep the original photo outside the public repository unless you want to publish it.

SVGs contain their own animations and a reduced-motion fallback. Some image viewers show a static frame; GitHub's image rendering is the intended target. All important information also has static text or image alternative text.

Local calendar refresh: `python scripts/update_contributions.py`.
