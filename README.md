<!-- Generated artwork. scripts/render_cards.py draws every card twice, cards/<name>-light.svg and
     -dark.svg, from data/content.json (the copy) and data/profile.json (contributions). The README
     shows white artwork while the sun is up in Bucharest and black after sunset: scripts/daynight.py
     rewrites the -light/-dark suffixes (and the badge colours), run by .github/workflows/profile.yml.
     Edit the JSON, not the SVGs. Keep this block free of blank lines. -->
<div align="center">
<img src="./cards/hero-light.svg" width="100%" alt="yolooo332. The name YOLOOO in coloured ASCII. Student at ACS, Politehnica Bucuresti, based in Bucharest, on Fedora plus a home cluster. Focus: ML systems, infra, security. Now: MedApp. Next: a FiveM framework in Rust." /><br>
<img src="./cards/ls-light.svg" width="100%" alt="ls ~/projects" /><br>
<img src="./cards/project-medapp-light.svg" width="100%" alt="MedApp, building: practice software for Romanian clinics contracted with CNAS. Offline-first, every CNAS call queued and archived. Rust, Axum, SQLite, Tauri 2, Svelte 5." /><br>
<a href="https://github.com/Andrei9383/uipath-hack"><img src="./cards/project-audiobolt-light.svg" width="100%" alt="AudioBolt, shipped at UiPath Future Forward with andrei9383: finds where a phone recording was made from the planes you can barely hear in it." /></a><br>
<img src="./cards/project-fivem-light.svg" width="100%" alt="Rust FiveM Framework, next week: a FiveM server framework written in Rust. Placeholder until work starts the week of Nov 23." /><br>
<img src="./cards/activity-light.svg" width="100%" alt="Contributions in the last 12 months as an ASCII heat grid, refreshed daily" /><br>
<img src="./cards/log-light.svg" width="100%" alt="git log: projects, newest first" />
</div>

---

<table>
<tr>
<td width="50%" valign="top">

<b>ML Systems Knowledge</b>

- **Pipeline parallelism**: splitting a model by layers across GPUs on different machines, 1F1B scheduling, keeping the pipeline bubble small
- **Parameter-efficient fine-tuning**: LoRA and QLoRA with PEFT, 4-bit quantization with bitsandbytes
- **Mixed precision**: bf16, fp16 and fp32 by GPU generation, dynamic loss scaling, fp32 residual streams
- **GPU memory planning**: budgeting weights, LoRA and optimizer state and activations per stage, gradient checkpointing, streaming layers from pinned RAM to train models bigger than VRAM
- **Training performance**: autocast, `torch.compile`, measuring throughput against baselines like Unsloth
- **SFT data**: chat templates, completion-only loss masking, sequence packing with per-document attention
- **Distributed correctness**: sending activations and gradients over TCP, gradient clipping across stages, checking split training against the unsplit model

</td>
<td width="50%" valign="top">

<b>Infra & AI Agents Knowledge</b>

- **Cluster scheduling**: placing jobs on GPU and CPU workers by memory, labels and taints; grid sweeps, pipelines and cron
- **Containers and sandboxing**: Docker and Podman images, running jobs as unprivileged users
- **Linux services**: systemd user units, self-updating workers, Postgres-backed state
- **Agent orchestration**: driving Claude Code and Codex agents from a task board, AI code review, automatic fixes for failed checks and merge conflicts
- **Model Context Protocol**: giving agents tools and a searchable knowledge base through an MCP server
- **CI/CD and Git workflows**: sandboxed lint, type and test checks, review-gated merges, Gitea to GitHub mirroring
- **TypeScript on Bun** for servers and CLIs

</td>
</tr>
<tr>
<td width="50%" valign="top">

<b>Security</b>

- Encrypted secrets, injected into each run and hidden from its logs
- Invite-based enrollment for workers and people, behind Cloudflare Access
- Encrypted backups of the cluster's state
- Threat modelling of the apps I build

</td>
<td width="50%" valign="top">

<b>Linux</b>

- Fedora as my daily driver, with Linux servers and workers running the home cluster
- Operating system modifications and new desktop features, coming to this profile soon

</td>
</tr>
</table>

---

<div align="center">
<img src="assets/stack-light.gif" alt="An ASCII atom: .c and .cpp, .lua and .java on two crossed orbits, the web languages on a wide equator, all circling a shaded core" width="100%">
</div>

<p align="center">
  <img src="https://img.shields.io/badge/python-ffffff?style=flat-square&logo=python&logoColor=2a74a3" alt="Python">
  <img src="https://img.shields.io/badge/rust-ffffff?style=flat-square&logo=rust&logoColor=2a74a3" alt="Rust">
  <img src="https://img.shields.io/badge/pytorch-ffffff?style=flat-square&logo=pytorch&logoColor=2a74a3" alt="PyTorch">
  <img src="https://img.shields.io/badge/hugging%20face-ffffff?style=flat-square&logo=huggingface&logoColor=2a74a3" alt="Hugging Face">
  <img src="https://img.shields.io/badge/bun-ffffff?style=flat-square&logo=bun&logoColor=2a74a3" alt="Bun">
  <img src="https://img.shields.io/badge/docker-ffffff?style=flat-square&logo=docker&logoColor=2a74a3" alt="Docker">
  <img src="https://img.shields.io/badge/linux-ffffff?style=flat-square&logo=linux&logoColor=2a74a3" alt="Linux">
  <br>
  <img src="https://img.shields.io/badge/c-ffffff?style=flat-square&logo=c&logoColor=2a74a3" alt="C">
  <img src="https://img.shields.io/badge/c++-ffffff?style=flat-square&logo=cplusplus&logoColor=2a74a3" alt="C++">
  <img src="https://img.shields.io/badge/c%23-ffffff?style=flat-square&logo=dotnet&logoColor=2a74a3" alt="C#">
  <img src="https://img.shields.io/badge/lua-ffffff?style=flat-square&logo=lua&logoColor=2a74a3" alt="Lua">
  <img src="https://img.shields.io/badge/java-ffffff?style=flat-square&logo=openjdk&logoColor=2a74a3" alt="Java">
  <img src="https://img.shields.io/badge/javascript-ffffff?style=flat-square&logo=javascript&logoColor=2a74a3" alt="JavaScript">
  <img src="https://img.shields.io/badge/typescript-ffffff?style=flat-square&logo=typescript&logoColor=2a74a3" alt="TypeScript">
  <img src="https://img.shields.io/badge/html5-ffffff?style=flat-square&logo=html5&logoColor=2a74a3" alt="HTML5">
  <img src="https://img.shields.io/badge/css3-ffffff?style=flat-square&logo=css&logoColor=2a74a3" alt="CSS3">
  <br>
  <img src="https://img.shields.io/badge/svelte-ffffff?style=flat-square&logo=svelte&logoColor=2a74a3" alt="Svelte">
  <img src="https://img.shields.io/badge/tauri-ffffff?style=flat-square&logo=tauri&logoColor=2a74a3" alt="Tauri">
  <img src="https://img.shields.io/badge/vue.js-ffffff?style=flat-square&logo=vuedotjs&logoColor=2a74a3" alt="Vue.js">
  <img src="https://img.shields.io/badge/vuetify-ffffff?style=flat-square&logo=vuetify&logoColor=2a74a3" alt="Vuetify">
  <img src="https://img.shields.io/badge/tailwindcss-ffffff?style=flat-square&logo=tailwindcss&logoColor=2a74a3" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/bootstrap-ffffff?style=flat-square&logo=bootstrap&logoColor=2a74a3" alt="Bootstrap">
  <img src="https://img.shields.io/badge/jquery-ffffff?style=flat-square&logo=jquery&logoColor=2a74a3" alt="jQuery">
  <br>
  <img src="https://img.shields.io/badge/sqlite-ffffff?style=flat-square&logo=sqlite&logoColor=2a74a3" alt="SQLite">
  <img src="https://img.shields.io/badge/mongodb-ffffff?style=flat-square&logo=mongodb&logoColor=2a74a3" alt="MongoDB">
  <img src="https://img.shields.io/badge/mysql-ffffff?style=flat-square&logo=mysql&logoColor=2a74a3" alt="MySQL">
  <img src="https://img.shields.io/badge/postgres-ffffff?style=flat-square&logo=postgresql&logoColor=2a74a3" alt="PostgreSQL">
</p>
