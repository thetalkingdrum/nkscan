# nkscan 0.14.1 full-roll drift vs Nikon Scan (LS-4000 ED + SA-30)

Scope: offline comparison of a Nikon Scan 4 SCSI capture and two nkscan 0.14.1 runs (`nkscan_666`, full roll; `nkscan_roll_thumbs`, thumbnail only) on the same 40-frame colour-negative roll. The roll was re-fed between Nikon Scan and nkscan. Labels: **[V]** = verified from bytes or code, **[I]** = inferred.

## Answer in one paragraph

nkscan's framing code does what Nikon Scan's does. Given Nikon's own thumbnail pass, nkscan 0.14.1 reproduces Nikon's 40-frame 8Fh table byte for byte **[V]**. The divergence comes earlier, in **the thumbnail pass the scanner delivers to nkscan**:

- In Nikon's pass, the 8Eh perforation records line up one-to-one with the image lines: 5822 records for 5822 lines of film **[V]**.
- In nkscan's pass, the scanner returned **5805 records for only 5785 lines of film** **[V]**. Record *i* therefore describes film about 0.35 % further along than image line *i*, and the error grows down the roll.

nkscan's search correctly finds every inter-frame gap in its image **[V]**. It then converts each gap line to a feed address through records that have slipped, so the frame starts lose about 17–23 addresses (≈0.1–0.15 mm) per frame, reaching −672 addresses (−4.3 mm, ≈12 % of a frame) by frame 40. Both nkscan runs show this identically **[V]**. Why the scanner produces an inconsistent pass for nkscan is not yet pinned down; the candidates are below.

## First divergence, stage by stage

| Stage | Nikon vs nkscan | Evidence |
|---|---|---|
| Frame count (`held`) | Same: 40 | Nikon's 8Fh count byte 0x28; nkscan `detected frames frames=40` **[V]** |
| 8Fh table length | Same: 40 records, 324 bytes, accepted by the unit; the 37-record/300-byte concern does not apply | SEND 8Fh seq 458 vs nkscan `cdb for send 8f` **[V]** |
| Thumbnail SET WINDOW | Identical (97 dpi, Y 0, length 250278, 14-bit) apart from exposure bytes | seq 328–332 vs nkscan TRACE payloads **[V]** |
| Thumbnail data | Same shape: 6104 lines, 3,515,904 bytes | **[V]** |
| **8Eh records vs image lines** | **Nikon: 5822 records (header) / film ends at line 5822. nkscan: 5805 records / film ends at line 5785 (+20)** | `data/gap_phase_*`, `tools/pass_check.py` **[V]** |
| Image line pitch | nkscan lines each cover 0.62–0.64 % more film than Nikon's; a smooth scale with no steps | `data/image_alignment_nkscan_to_nikon.txt` (Nikon line ≈ 1.0062 × nkscan line) **[V]** |
| Search (`search`, `adjust`) | Faithful. On Nikon's pass the output equals Nikon's table; on nkscan's pass the starts of frames 4–40 sit 0–2 lines after a real gap end (frame 39 borders a wide gap) | tests below; `data/gap_phase_nkscan_pass.txt` **[V]** |
| `resample`, `table` | Faithful. On this LS-4000 roll `resample` keeps every line (perforations are 17–19 lines, k = 18) | Python port reproduces nkscan's sent table 40/40 **[V]** |
| Fine scans | Same model in both: 8Fh sent once, each frame windowed at its table top, no `register()` off-table frames | Nikon Y origins ⊂ table tops; nkscan 40/40 windows = table tops; 0 `registered a frame` lines **[V]** |

Perforation phase (address mod 6048) of the first line after each gap, per pass:

- **Nikon**: about 1820 from frame 5 to frame 40, steady.
- **nkscan**: 1848 → 1246, steady decline.

The gaps on the film sit at a constant perforation phase, so the error is in nkscan's records-to-lines pairing, not in its gap finding.

## Per-frame evidence (thumbnail-only run vs Nikon's table)

Δ is nkscan − Nikon in feed addresses (1 address = 1/4000 in). One resampled line is 42 addresses. Frames 1–4 are leader, which both tools fill with irregular frames. Perforation numbers are only loosely comparable across a re-feed; the phase argument above does not depend on them.

| # | Nikon top | Nikon perf.dec.pulse | nkscan top | nkscan perf.dec.pulse | Δ addr | Δ mm | Δ resampled lines |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | 42 | 0.0.6 | 42 | 0.0.6 | +0 | +0.00 | +0.0 |
| 2 | 4242 | 5.2.22 | 7630 | 10.0.10 | +3388 | +21.51 | +80.7 |
| 3 | 11242 | 14.4.6 | 13496 | 17.4.4 | +2254 | +14.31 | +53.7 |
| 4 | 19446 | 25.3.12 | 20020 | 26.1.30 | +574 | +3.64 | +13.7 |
| 5 | 25984 | 34.1.18 | 26096 | 34.1.34 | +112 | +0.71 | +2.7 |
| 6 | 32018 | 42.1.16 | 32130 | 42.1.32 | +112 | +0.71 | +2.7 |
| 7 | 38080 | 50.1.18 | 38178 | 50.1.32 | +98 | +0.62 | +2.3 |
| 8 | 44100 | 58.1.14 | 44184 | 58.1.26 | +84 | +0.53 | +2.0 |
| 9 | 50134 | 66.1.12 | 50190 | 66.1.20 | +56 | +0.36 | +1.3 |
| 10 | 56210 | 74.1.16 | 56224 | 74.1.18 | +14 | +0.09 | +0.3 |
| 11 | 62244 | 82.1.14 | 62244 | 82.1.14 | +0 | +0.00 | +0.0 |
| 12 | 68306 | 90.1.16 | 68250 | 90.1.8 | -56 | -0.36 | -1.3 |
| 13 | 74368 | 98.1.18 | 74298 | 98.1.8 | -70 | -0.44 | -1.7 |
| 14 | 80402 | 106.1.16 | 80318 | 106.1.4 | -84 | -0.53 | -2.0 |
| 15 | 86478 | 114.1.20 | 86394 | 114.1.8 | -84 | -0.53 | -2.0 |
| 16 | 92526 | 122.1.20 | 92442 | 122.1.8 | -84 | -0.53 | -2.0 |
| 17 | 98532 | 130.1.14 | 98420 | 130.0.20 | -112 | -0.71 | -2.7 |
| 18 | 104608 | 138.1.18 | 104482 | 138.0.22 | -126 | -0.80 | -3.0 |
| 19 | 110656 | 146.1.18 | 110474 | 146.0.14 | -182 | -1.16 | -4.3 |
| 20 | 116676 | 154.1.14 | 116466 | 154.0.6 | -210 | -1.33 | -5.0 |
| 21 | 122724 | 162.1.14 | 122528 | 162.0.8 | -196 | -1.24 | -4.7 |
| 22 | 128786 | 170.1.16 | 128534 | 170.0.2 | -252 | -1.60 | -6.0 |
| 23 | 134820 | 178.1.14 | 134484 | 177.4.8 | -336 | -2.13 | -8.0 |
| 24 | 140910 | 186.1.20 | 140518 | 185.4.6 | -392 | -2.49 | -9.3 |
| 25 | 146944 | 194.1.18 | 146580 | 193.3.30 | -364 | -2.31 | -8.7 |
| 26 | 152950 | 202.1.12 | 152586 | 201.4.2 | -364 | -2.31 | -8.7 |
| 27 | 159040 | 210.1.18 | 158648 | 209.3.26 | -392 | -2.49 | -9.3 |
| 28 | 165074 | 218.1.16 | 164682 | 217.3.24 | -392 | -2.49 | -9.3 |
| 29 | 171080 | 226.1.10 | 170660 | 225.3.14 | -420 | -2.67 | -10.0 |
| 30 | 177142 | 234.1.12 | 176750 | 233.3.20 | -392 | -2.49 | -9.3 |
| 31 | 183218 | 242.1.16 | 182756 | 241.3.14 | -462 | -2.93 | -11.0 |
| 32 | 189266 | 250.1.16 | 188818 | 249.3.16 | -448 | -2.84 | -10.7 |
| 33 | 195314 | 258.1.16 | 194796 | 257.3.6 | -518 | -3.29 | -12.3 |
| 34 | 201362 | 266.1.16 | 200858 | 265.3.8 | -504 | -3.20 | -12.0 |
| 35 | 207438 | 274.1.20 | 206864 | 273.3.2 | -574 | -3.64 | -13.7 |
| 36 | 213528 | 282.2.4 | 212842 | 281.1.36 | -686 | -4.36 | -16.3 |
| 37 | 219506 | 290.1.16 | 218834 | 289.2.6 | -672 | -4.27 | -16.0 |
| 38 | 225596 | 298.1.22 | 224854 | 297.2.2 | -742 | -4.71 | -17.7 |
| 39 | 231602 | 306.1.16 | 230944 | 305.1.30 | -658 | -4.18 | -15.7 |
| 40 | 237678 | 314.1.20 | 236992 | 313.1.30 | -686 | -4.36 | -16.3 |

The `nkscan_666` run follows the same trend, within ±160 addresses frame by frame and also −672 at frame 40 (`data/per_frame_tables.txt`).

## Fixture and tests (on the Mac only: branch `scratch/full-roll-drift` in ~/nkscan, uncommitted; not in this fork because the fixtures hold the roll's images)

- `tests/fixtures/framing/ls4000_sa30_full_roll/`: Nikon's thumbnail (rebuilt from the image READs), Nikon's 8Eh, and Nikon's 8Fh SEND.
  - Nikon reads 8Eh with the header's length, 6 bytes short of the record. The fixture keeps the 5820 whole records Nikon received and sets the parameter length to match.
- `tests/fixtures/framing/ls4000_sa30_full_roll_nkscan_pass/`: nkscan's thumbnail from its TIFF, with the 16-bit stretch inverted exactly and the unfilled tail restored. Also nkscan's 8Eh from the log, and the 8Fh nkscan sent.
- Tests in `src/scan/boundary/perforation/tests.rs`:
  - `a_full_sa30_roll_is_framed_as_nikon_frames_it`: **passes**. Byte-identical to Nikon's table.
  - `a_full_sa30_roll_keeps_its_frames_on_one_perforation_phase`: **passes**. Spread 112 addresses.
  - `nkscans_own_sa30_pass_replays_to_the_table_it_sent`: **passes**. The replay reproduces the live run.
  - `nkscans_sa30_pass_keeps_its_frames_on_one_perforation_phase`: **fails**. Drift of 812 addresses. This is the reproduction.
- Run with `cargo test --lib perforation`.

The fixtures contain the roll's thumbnail (personal images). They have not been uploaded anywhere.

## Why the scanner's pass differs: candidates (all [I], untested)

These are the differences between the two command streams up to and including the thumbnail SCAN:

1. **READ size.**
   - nkscan reads the thumbnail in 131072-byte chunks. That is not a whole number of 576-byte lines (3 colours × 96 px × 2 bytes).
   - Nikon reads 130752 bytes (227 lines) at a time.
   - This unit's VPD C1h byte 4 is 01h, so it doesn't *require* line units. The LS-5000 spec does require them on other units (2-11 SCSI function support, bit 1).
2. **Exposure.**
   - nkscan's thumbnail exposures are R 59299 / G 105165 / B 115646.
   - Nikon's are 57616 / 103751 / 114022.
   - Both are the start-up 8Ch value × the same factors (1.231 / 2.844 / 3.839); the 8Ch readings differed between sessions.
   - A longer line time would explain why each line covers more film. It wouldn't by itself explain the records outrunning the image.
3. **Gamma LUTs.** Nikon sends three `SEND dtc=03` LUTs (32 KB each) before the thumbnail; nkscan sends none.
4. **Focus move.** nkscan executes FocusMove (C1h) to 217 before the thumbnail; Nikon does not move focus.
5. **Ruled out.** Nikon's `E0 B4h` (`00 00 00 0e 10 …`) is the medium-ejection timer, 3600 s (LS5kIFSpec 2-11). DriverVersion (SEND 92h) is likewise irrelevant.

Proposed hardware runs, one change each. Run thumbnail-only and check each with `tools/pass_check.py <log> <thumbnail.tiff>`; a good pass gives records − lines = 0 and a phase trend near 0.

- A. Thumbnail READ length rounded down to whole lines (227 × 576).
- B. Send the three LUTs before the thumbnail.
- C. Skip the pre-thumbnail FocusMove.
- D. Repeat stock nkscan twice, to confirm the +20 is systematic. It already appears in both runs here: 5801 and 5805 records.

A host-side mitigation is possible but is not Nikon's behaviour: map image line *i* to record `round(i × records / filled_lines)`. On this pass that cuts the drift from about 600 to about 150 addresses, which is partial **[V]**.

## Corrections to the handover

- The unit is an **LS-4000 ED, firmware 1.10**, not an LS-50.
- The nkscan Windows logs *do* contain the full 8Eh `recv` and 8Fh `send` bytes (DEBUG lines) and every CDB, but not image data.
- nkscan's thumbnail TIFF is 16-bit, stretched from 14-bit and cut at the last filled column. Because `resample` keeps every line on this roll, it is a lossless copy of the pass, so it *can* be replayed.

## Files

- `tools/srec.py`: SREC parser. `inventory` prints one line per command; `dump` writes one payload.
- `data/nikon_inventory.txt`: the inventory dump. Quiet TURs are collapsed.
- `tools/pass_check.py`: one-pass consistency check for future nkscan runs.
- `tools/make_fixture.py`, `tools/make_nk_fixture.py`: fixture builders.
- `tools/resample.py`: line-for-line Python port of `resample.rs`.
- The other `tools/*.py` and `data/*.txt` are the analyses cited above.

## Result of the hardware runs (2026-10-16, same roll, same session, stock build vs `NKSCAN_EXP_WHOLE_LINES=1`)

| | Run 0 (stock) | Run A (whole-line reads) |
|---|---|---|
| Thumbnail READ size | 131072 bytes (ends partway through a line) | 130752 bytes (227 × 576) |
| 8Eh records vs filled lines | 5826 vs 5807, **surplus +19** | 5828 vs 5828, **surplus 0** |
| Frame phase spread, frames 6–40 | **840**, steady fall 1890 → 1134 | **84**, flat 1848–1932 |
| Thumbnail exposure R/G/B | 55848 / 101869 / 111887 | identical |

**[V]** With exposure byte-identical, the READ length is the only difference between the runs. Whole-line READs make the scanner's 8Eh records match the image line for line, as in Nikon Scan's pass, and the frames hold one perforation phase down the roll.

Exposure (candidate 2) is ruled out: Run 0's exposure was lower than Nikon's and the pass still drifted. Candidates 3 and 4 are moot.

**Cause:** nkscan reads the image with lengths that are not a whole number of lines whenever the unit does not flag the requirement. On this LS-4000 ED (fw 1.10) the VPD C1h byte 4 is 01h, so the line bit is clear. Nikon Scan reads whole lines regardless. On the SA-30 thumbnail, partial-line READs make the perforation records outrun the image by about 20 lines over a roll.

**Fix direction:** in `read_granules` (`src/protocol/image.rs`), always read in whole lines across every colour. A full-roll scan with the switch on looks right so far; confirmation is pending the end of that roll.
