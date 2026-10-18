"""Build the poster-sample videos shown on the OPERA project page.

Two videos are produced, one per sample used in the IUS 2026 poster:

  1. phantom  - blue/black wire phantom, 4 wavelengths at 20 Hz (poster Fig. 2).
                Rendered from the per-frame ratio stream and the shift test
                stored in step2_step3_results.mat.
  2. heart    - ex vivo porcine heart RF ablation, 5 wavelengths at 20 Hz
                (poster Fig. 3). Rendered from the exact overlay frames used
                to build the poster figure.

The raw inputs are lab data and are NOT part of this repository. Pass their
locations on the command line. Every run writes docs/media/manifest.json with
input and output SHA-256 hashes, the toolkit commit, and the numbers quoted on
the page, so each published clip can be traced back to its inputs.

Usage:
    python tools/media/build_poster_videos.py \
        --phantom-mat  <.../step2_step3_results.mat> \
        --heart-frames <.../fig3_frames_overlay>

Requires: numpy, h5py, matplotlib, pillow, and ffmpeg on PATH.
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import subprocess
import tempfile

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.animation import FFMpegWriter  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "docs", "media")
FONT_DIR = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
FONT = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

W, H, FPS = 1280, 720, 30
INK = "#1b1f24"
MUTED = "#5b6470"
RULE = "#d0d5db"
ACCENT = "#c2410c"
WL_COLORS = {700: "#2563eb", 740: "#dc2626", 760: "#16a34a", 780: "#7c3aed"}
SHIFT_COLORS = {-2: "#0072bd", -1: "#d95319", 1: "#77ac30", 2: "#7e2f8e"}

SITE_URL = "ryomurakami-medrobo.github.io/OPERA_Realtime-Multiwavelength-PA-Toolkit"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head():
    try:
        return subprocess.check_output(
            ["git", "-C", REPO, "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def probe_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], text=True)
    return round(float(out.strip()), 2)


def r_squared(y, ref):
    y, ref = np.asarray(y), np.asarray(ref)
    ss_res = np.sum((y - ref) ** 2)
    ss_tot = np.sum((ref - ref.mean()) ** 2)
    return float(1 - ss_res / ss_tot)


# --------------------------------------------------------------------------
# Phantom
# --------------------------------------------------------------------------

def load_phantom(path):
    with h5py.File(path, "r") as f:
        g = lambda k: np.array(f[k]).squeeze()  # noqa: E731
        return {
            "wl": g("common_wl_sorted").astype(int),
            "shifts": g("shift_values").astype(int),
            "shift_spec": np.array(f["step3_shift_spectrum"]).T,
            "shift_std": np.array(f["step3_shift_spectrum_std"]).T,
            "ref": g("ref_mu_common"),
            "label": g("sequence_label_nm").astype(int),
            "ratio": g("sequence_ratio"),
            "count": g("sequence_success_count").astype(int),
        }


def build_phantom(mat_path, out_mp4, stream_seconds=24.0, shift_seconds=8.0):
    d = load_phantom(mat_path)
    wl, ref = d["wl"], d["ref"]
    n = len(d["ratio"])
    stream_frames = int(stream_seconds * FPS)
    shift_frames = int(shift_seconds * FPS)
    per_video_frame = n / stream_frames
    playback = per_video_frame * FPS / 20.0  # source is 20 Hz
    s0 = list(d["shifts"]).index(0)
    r2_tagged = r_squared(d["shift_spec"][s0], ref)

    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor="white")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                         "axes.edgecolor": RULE, "axes.labelcolor": INK,
                         "xtick.color": MUTED, "ytick.color": MUTED})
    fig.text(0.04, 0.945, "OPERA  |  Wire phantom, deterministic wavelength tagging",
             fontsize=19, weight="bold", color=INK)
    fig.text(0.04, 0.905, "Blue / black wire  ·  λ = 700, 740, 760, 780 nm  ·  20 Hz  ·  "
             "same data as poster Fig. 2", fontsize=12.5, color=MUTED)
    footer = fig.text(0.04, 0.03, "", fontsize=11, color=MUTED)
    fig.text(0.96, 0.03, SITE_URL, fontsize=11, color=MUTED, ha="right")

    ax_s = fig.add_axes([0.06, 0.17, 0.50, 0.62])
    ax_p = fig.add_axes([0.64, 0.17, 0.32, 0.62])
    counter = fig.text(0.06, 0.815, "", fontsize=14, color=INK, family="DejaVu Sans Mono")

    window = 60
    ax_s.set_ylim(1.6, 5.2)
    ax_s.set_xlabel("Laser pulse count  C$_{laser}$ (from MCU)")
    ax_s.set_ylabel("Intensity ratio  I$_{blue}$ / I$_{black}$")
    ax_s.grid(color="#eef0f2")
    scat = ax_s.scatter([], [], s=34, zorder=3)
    for w in wl:
        ax_s.scatter([], [], s=34, color=WL_COLORS[w], label=f"tagged {w} nm")
    ax_s.legend(loc="upper left", ncol=4, frameon=False, fontsize=10.5, columnspacing=0.8,
                bbox_to_anchor=(0, 1.0))

    ax_p.set_xlim(690, 790)
    ax_p.set_ylim(1.6, 5.2)
    ax_p.set_xticks(wl)
    ax_p.set_xlabel("Wavelength [nm]")
    ax_p.set_title("Running spectrum", fontsize=13, color=INK, loc="left")
    ax_p.grid(color="#eef0f2")
    ax_p.plot(wl, ref, "-s", color="#d62728", lw=2.2, ms=7, mfc="#fbd0d0",
              label="Reference (independent run)", zorder=2)
    (run_line,) = ax_p.plot([], [], "-o", color=INK, lw=2.6, ms=8, mfc="#9aa0a6",
                            label="OPERA tagged (shift 0)", zorder=4)
    shift_lines = {}
    # With 4 wavelengths a +2 and a -2 slip give identical labels: draw one curve.
    shift_labels = {-1: "shift -1", 1: "shift +1", 2: "shift ±2 (identical)"}
    for s in [-1, 1, 2]:
        (ln,) = ax_p.plot([], [], "--", color=SHIFT_COLORS[s], lw=1.6,
                          label=shift_labels[s], zorder=1)
        shift_lines[s] = ln
    ax_p.legend(loc="lower left", bbox_to_anchor=(0, 0.13), frameon=False, fontsize=9.5)
    note = ax_p.text(0.02, 0.03, "", transform=ax_p.transAxes, fontsize=10.5, color=INK)

    sums = {w: 0.0 for w in wl}
    cnts = {w: 0 for w in wl}
    state = {"i": 0}

    def draw(frame):
        if frame < stream_frames:
            hi = min(n, int(round((frame + 1) * per_video_frame)))
            for k in range(state["i"], hi):
                sums[d["label"][k]] += d["ratio"][k]
                cnts[d["label"][k]] += 1
            state["i"] = hi
            lo = max(0, hi - window)
            xs = d["count"][lo:hi]
            ys = d["ratio"][lo:hi]
            cs = [WL_COLORS[v] for v in d["label"][lo:hi]]
            scat.set_offsets(np.c_[xs, ys])
            scat.set_color(cs)
            last = d["count"][hi - 1]
            ax_s.set_xlim(last - window + 0.5, last + 1.5)
            counter.set_text(f"C_laser = {last:4d}  ->  tagged {d['label'][hi - 1]} nm"
                             f"    ({hi} / {n} frames)")
            means = [sums[w] / cnts[w] if cnts[w] else np.nan for w in wl]
            run_line.set_data(wl, means)
            footer.set_text(f"Acquisition time {hi / 20:5.1f} s   ·   playback {playback:.1f}x")
        else:
            k = frame - stream_frames
            order = [-1, 1, 2]
            shown = order[: min(3, 1 + k // int(1.2 * FPS))]
            for s in shift_lines:
                if s in shown:
                    shift_lines[s].set_data(wl, d["shift_spec"][list(d["shifts"]).index(s)])
            note.set_text(f"If one pulse were miscounted, labels slip by ±1 or ±2\n"
                          f"and the 740 nm peak moves.  OPERA tags: R² = {r2_tagged:.3f}")
            footer.set_text("Shift test: labels deliberately offset by ±1, ±2 frames "
                            "(as in poster Fig. 2)")
        return ()

    writer = FFMpegWriter(fps=FPS, codec="libx264", bitrate=-1,
                          extra_args=["-pix_fmt", "yuv420p", "-crf", "23",
                                      "-preset", "slow", "-movflags", "+faststart"])
    with writer.saving(fig, out_mp4, dpi=100):
        for frame in range(stream_frames + shift_frames):
            draw(frame)
            writer.grab_frame()
    plt.close(fig)

    return {
        "frames_in_source": int(n),
        "acquisition_seconds": n / 20.0,
        "playback_speed": round(playback, 1),
        "wavelengths_nm": [int(w) for w in wl],
        "r2_tagged_vs_reference": round(r2_tagged, 4),
        "tagged_spectrum": [round(float(v), 3) for v in d["shift_spec"][s0]],
        "reference_spectrum": [round(float(v), 3) for v in ref],
    }


# --------------------------------------------------------------------------
# Porcine heart
# --------------------------------------------------------------------------

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def build_heart(frames_dir, out_mp4, hold=0.5, total_sec=250.0):
    with open(os.path.join(frames_dir, "frame_index.csv"), newline="") as f:
        rows = list(csv.DictReader(f))
    tmp = tempfile.mkdtemp(prefix="opera_heart_")
    scale = 1.12
    for i, r in enumerate(rows):
        im = Image.open(os.path.join(frames_dir, r["file"])).convert("RGB")
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        canvas = Image.new("RGB", (W, H), "white")
        dr = ImageDraw.Draw(canvas)
        dr.text((40, 16), "OPERA  |  Ex vivo porcine heart, real-time RF ablation monitoring",
                font=font(25, True), fill=INK)
        dr.text((40, 50), "5 wavelengths (700, 710, 720, 840, 850 nm) at 20 Hz  ·  "
                "spectral unmixing heat map  ·  same frames as poster Fig. 3",
                font=font(16), fill=MUTED)
        canvas.paste(im, ((W - im.width) // 2, 78))
        t = float(r["elapsed_sec"])
        y = H - 34
        x0, x1 = 40, W - 40
        dr.line([(x0, y), (x1, y)], fill=RULE, width=6)
        dr.line([(x0, y), (x0 + (x1 - x0) * t / total_sec, y)], fill=ACCENT, width=6)
        dr.text((x0, y + 8), f"Ablation time {t:5.1f} s  ·  package {r['package_index']}  ·  "
                f"playback {total_sec / (len(rows) * hold):.0f}x",
                font=font(14), fill=MUTED)
        dr.text((x1, y + 8), SITE_URL, font=font(14), fill=MUTED, anchor="ra")
        canvas.save(os.path.join(tmp, f"f{i:03d}.png"))
    ffmpeg("-framerate", str(1 / hold), "-i", os.path.join(tmp, "f%03d.png"),
           "-vf", f"fps={FPS}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "22", "-preset", "slow", "-movflags", "+faststart", out_mp4)
    packages = [int(r["package_index"]) for r in rows]
    missing = sorted(set(range(1, max(packages) + 1)) - set(packages))
    return {
        "frames_in_source": len(rows),
        "packages_shown": f"{min(packages)}-{max(packages)}",
        "packages_not_in_poster_set": missing,
        "ablation_seconds_covered": round(float(rows[-1]["elapsed_sec"]), 1),
        "playback_speed": round(total_sec / (len(rows) * hold)),
        "wavelengths_nm": [700, 710, 720, 840, 850],
        "input_frame_hashes": {r["file"]: sha256(os.path.join(frames_dir, r["file"]))
                               for r in rows},
    }


# --------------------------------------------------------------------------
# Derivatives: poster image, square social cut
# --------------------------------------------------------------------------

def still(mp4, png, at):
    ffmpeg("-ss", str(at), "-i", mp4, "-frames:v", "1", png)


def square_cut(mp4, out_mp4, headline, sub, crop_top):
    """1080x1080 version for LinkedIn / X feeds: headline above, URL below."""
    bg = os.path.join(tempfile.mkdtemp(prefix="opera_sq_"), "bg.png")
    im = Image.new("RGB", (1080, 1080), "white")
    dr = ImageDraw.Draw(im)
    dr.text((60, 70), headline, font=font(46, True), fill=INK)
    dr.text((60, 140), sub, font=font(26), fill=MUTED)
    dr.line([(60, 930), (1020, 930)], fill=RULE, width=2)
    dr.text((60, 955), "Open-source  ·  MIT  ·  github.com/RyoMurakami-MedRobo",
            font=font(24), fill=MUTED)
    dr.text((60, 995), "OPERA_Realtime-Multiwavelength-PA-Toolkit", font=font(24, True), fill=INK)
    im.save(bg)
    ffmpeg("-loop", "1", "-i", bg, "-i", mp4, "-filter_complex",
           f"[1:v]crop=iw:ih-{crop_top}:0:{crop_top},scale=1080:-2[v];"
           "[0:v][v]overlay=0:(H-h)/2+10:shortest=1",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
           "-movflags", "+faststart", out_mp4)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--phantom-mat", required=True)
    ap.add_argument("--heart-frames", required=True)
    args = ap.parse_args()
    os.makedirs(os.path.join(OUT, "social"), exist_ok=True)

    clips = []

    p_mp4 = os.path.join(OUT, "opera_phantom_tagging.mp4")
    p_meta = build_phantom(args.phantom_mat, p_mp4)
    still(p_mp4, os.path.join(OUT, "opera_phantom_tagging.jpg"), 27)
    square_cut(p_mp4, os.path.join(OUT, "social", "opera_phantom_square.mp4"),
               "Every laser pulse, counted.",
               "An external MCU tags each frame with its wavelength.", crop_top=100)
    clips.append(("phantom", p_mp4, "opera_phantom_tagging.jpg",
                  {"sha256": sha256(args.phantom_mat),
                   "file": os.path.basename(args.phantom_mat),
                   "dataset": "Packaging validation 2026-04-03, run r5 vs standard 2 "
                              "(analysis run 2026-04-22 16:41)"}, p_meta))

    h_mp4 = os.path.join(OUT, "opera_heart_ablation.mp4")
    h_meta = build_heart(args.heart_frames, h_mp4)
    still(h_mp4, os.path.join(OUT, "opera_heart_ablation.jpg"), 16)
    square_cut(h_mp4, os.path.join(OUT, "social", "opera_heart_square.mp4"),
               "Watching an RF ablation grow.",
               "Ex vivo porcine heart, 5 wavelengths, 20 Hz.", crop_top=72)
    frame_hashes = h_meta.pop("input_frame_hashes")
    clips.append(("heart", h_mp4, "opera_heart_ablation.jpg",
                  {"sha256": sha256(os.path.join(args.heart_frames, "frame_index.csv")),
                   "file": "frame_index.csv + 49 overlay PNGs",
                   "frame_sha256": frame_hashes,
                   "dataset": "Ex vivo porcine heart RF ablation, IUS 2026 poster Fig. 3 frame set"},
                  h_meta))

    manifest = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "toolkit_commit": git_head(),
        "script": "tools/media/build_poster_videos.py",
        "clips": [],
    }
    for cid, mp4, poster, src, meta in clips:
        manifest["clips"].append({
            "id": cid,
            "video": os.path.relpath(mp4, os.path.join(REPO, "docs")).replace("\\", "/"),
            "poster": "media/" + poster,
            "duration_s": probe_duration(mp4),
            "bytes": os.path.getsize(mp4),
            "sha256": sha256(mp4),
            "source": src,
            **meta,
        })
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(json.dumps({c["id"]: {k: c[k] for k in ("duration_s", "bytes", "playback_speed")}
                      for c in manifest["clips"]}, indent=2))


if __name__ == "__main__":
    main()
