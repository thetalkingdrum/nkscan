# Handover: SA-30 thumbnail drift experiment (Windows machine)

Branch `experiment/sa30-thumbnail-drift` in `thetalkingdrum/nkscan` is nkscan 0.14.1 plus two
experiment switches and one extra log line. Background and evidence: [FINDINGS.md](FINDINGS.md).
If you are a Claude session picking this up, read FINDINGS.md first. Do not drive the scanner
yourself; Mats runs the scans and hands you the logs.

## Where things stand

- nkscan's framing code reproduces Nikon Scan byte for byte, given Nikon's thumbnail pass.
- The drift comes from the thumbnail pass the LS-4000 + SA-30 returns to nkscan.
  - Its 8Eh perforation records outnumber the lines of film in the image: 5805 records for 5785 lines, a surplus of +20.
  - Nikon Scan's pass has 5822 of each, a surplus of 0.
  - Frames found on the image's gaps therefore land on drifting perforation addresses, about −4.3 mm by frame 40.
- Cause not yet proven. The two best guesses are tested here:
  - **A**: nkscan's 131072-byte image READs end partway through a 576-byte line. Nikon reads whole lines (227 × 576 = 130752).
  - **B**: thumbnail exposure. Nikon's pass used R/G/B 57616 / 103751 / 114022; nkscan's used 59299 / 105165 / 115646.

## Get the binary

- Download the `nkscan-exp-windows` artifact from the latest run of **Experiment Windows build**: <https://github.com/thetalkingdrum/nkscan/actions>. It is rebuilt on every push to this branch.
- Or, with gh:

  ```
  gh run download -R thetalkingdrum/nkscan -n nkscan-exp-windows
  ```

  You need to be logged in to GitHub.

Check that the binary is the experiment build: `nkscan.exe --version` shows `exp-<commit>`.

## Runs

Use `cmd.exe`. PowerShell 5 mangles native stderr redirected to a file.

Load the same roll once and keep it loaded. Do one thumbnail plus frame 1 per run; `--frames 1` keeps each run short. Clear the variables between runs.

```
:: 0. Control: stock behaviour, expect surplus +20
set NKSCAN_EXP_WHOLE_LINES=
set NKSCAN_EXP_THUMB_EXPOSURE=
nkscan.exe scan --log debug --thumbnail --no-eject --frames 1 --dpi 666 --basename run0 2> run0.log

:: A. Whole-line READs
set NKSCAN_EXP_WHOLE_LINES=1
nkscan.exe scan --log debug --thumbnail --no-eject --frames 1 --dpi 666 --basename runA 2> runA.log
set NKSCAN_EXP_WHOLE_LINES=

:: B. Nikon's thumbnail exposures
set NKSCAN_EXP_THUMB_EXPOSURE=57616,103751,114022
nkscan.exe scan --log debug --thumbnail --no-eject --frames 1 --dpi 666 --basename runB 2> runB.log
set NKSCAN_EXP_THUMB_EXPOSURE=

:: AB. Both, only if A and B each help partly
set NKSCAN_EXP_WHOLE_LINES=1
set NKSCAN_EXP_THUMB_EXPOSURE=57616,103751,114022
nkscan.exe scan --log debug --thumbnail --no-eject --frames 1 --dpi 666 --basename runAB 2> runAB.log
```

`--log debug` is enough; it carries the 8Eh and 8Fh bytes. `--log trace` also works but is much bigger.

If a run's log doesn't contain an `experiment:` line for the switch you set, the variable didn't reach nkscan.exe.

## Reading the result

Each log contains this line:

```
experiment: 8Eh records against filled thumbnail lines records=… filled=… surplus=…
```

- **surplus 0**: a good pass. That variant fixes it.
- **surplus about +20**: unchanged.

For the frame positions as well (needs Python 3, no packages):

```
python experiment\tools\log_check.py run0.log
```

- Good: phase spread about 100–130.
- Stock nkscan on this roll: about 800, falling steadily.

`tools\pass_check.py <log> <basename>_1_thumbnail.tiff` does the same from the thumbnail image. It needs numpy.

## What to do with the outcome

- **A fixes it**: nkscan should read in whole lines even where this unit's VPD C1h doesn't demand it (byte 4 = 01h). The change belongs in `read_granules` in `src/protocol/image.rs`.
- **B fixes it**: the pass depends on exposure, i.e. line time. Nikon Scan may then drift too on other days, which is a firmware quirk. Check by repeating Nikon Scan captures with the SCSI proxy.
- **Neither**: the next candidates are sending Nikon's gamma LUTs (`SEND dtc=03`, three 32 KB tables) before the thumbnail, and skipping the FocusMove (C1h) nkscan does before it. See FINDINGS.md, "Why the scanner's pass differs".

Mats reports upstream (activexray/nkscan) himself, in his own words.

## Files here

- `FINDINGS.md`: the full write-up, with a per-frame table.
- `tools/log_check.py`: judges a run from its log only.
- `tools/pass_check.py`: judges a run from its log plus thumbnail TIFF.
- `tools/srec.py`: parser for the NKDSBP2 proxy's `scsi_trace.bin`. Run `inventory` for a command listing.
- `tools/*.py` (the rest): the analyses behind FINDINGS.md. Several need the Nikon capture, which is not in this repo.
- `data/`: Nikon command inventory, per-frame tables, and alignment outputs. Text only; no images.

The thumbnail fixtures and the replay tests stay on the Mac (`~/nkscan`, branch `scratch/full-roll-drift`) because they contain the roll's images.
