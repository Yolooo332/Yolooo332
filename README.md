<div align="center">

<img src="assets/hero.gif" alt="YOLOOO, rendered as animated ASCII in JetBrains Mono: the name ignites under a scan beam, holds, then burns off into embers" width="100%">

</div>

<p align="center"><img src="assets/h-description.svg" alt="Description" width="100%"></p>

<div align="center">

**Machine learning systems**, **self-hosted infrastructure** and **security**, on Linux.<br>
<sub>Student at Politehnica București, <i>Automatică și Calculatoare</i> · Bucharest, Romania</sub>

</div>

<table>
<tr>
<td width="50%" valign="top">

<b>ML systems</b><br>
<sub><i>from an LLM training project, launching soon</i></sub>

- **Pipeline-parallel fine-tuning**: one model split by layers across GPUs in different machines, with 1F1B scheduling so the cards overlap instead of taking turns
- **QLoRA with PEFT + bitsandbytes 4-bit**, and per-GPU precision (bf16, fp16, fp32) with one dynamic loss scale for the whole chain
- **A memory-first planner** that estimates VRAM per stage and picks the split where the slowest GPU is fastest, using each card's measured speed
- **Streaming layers from pinned RAM**: a 32B model fine-tuned on a single 12 GB RTX 5070
- **0.92× Unsloth's per-GPU speed** on a 7B, with 16-bit autocast and per-layer `torch.compile`
- **A custom framed TCP protocol** for activations and gradients, plus tests showing split training gives the same losses and LoRA weights as the unsplit model

</td>
<td width="50%" valign="top">

<b>Infra & AI agents</b><br>
<sub><i>from my self-hosted home cluster, launching soon</i></sub>

- **A cluster for people and coding agents**: a Bun + TypeScript server on Postgres that schedules jobs onto GPU and CPU workers across my machines
- **Scheduling with GPU-memory requests**, labels and taints, hyperparameter grid sweeps, multi-step pipelines and cron
- **Sandboxed runs** in Docker or Podman, with workers running as self-updating systemd user units
- **Agent orchestration**: Claude Code and Codex agents take tasks from a board, push their work, get an AI review, and auto-fix failed checks and merge conflicts
- **An MCP server and a knowledge base** so agents can search past runs and notes
- **CI before main**: lint, typing and tests run in a sandbox, merges are gated on review, and the repo is mirrored from Gitea to GitHub

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

<p align="center"><img src="assets/h-options.svg" alt="Options" width="100%"></p>

<div align="center">
<img src="assets/stack.gif" alt="An ASCII atom: .c and .cpp, .lua and .java on two crossed orbits, the web languages on a wide equator, all circling a shaded core" width="100%">
</div>

<p align="center">
  <img src="https://img.shields.io/badge/python-0d1117?style=flat-square&logo=python&logoColor=ffd43b" alt="Python">
  <img src="https://img.shields.io/badge/pytorch-0d1117?style=flat-square&logo=pytorch&logoColor=ee4c2c" alt="PyTorch">
  <img src="https://img.shields.io/badge/hugging%20face-0d1117?style=flat-square&logo=huggingface&logoColor=ffd21e" alt="Hugging Face">
  <img src="https://img.shields.io/badge/bun-0d1117?style=flat-square&logo=bun&logoColor=fbf0df" alt="Bun">
  <img src="https://img.shields.io/badge/docker-0d1117?style=flat-square&logo=docker&logoColor=2496ed" alt="Docker">
  <img src="https://img.shields.io/badge/linux-0d1117?style=flat-square&logo=linux&logoColor=fcc624" alt="Linux">
  <br>
  <img src="https://img.shields.io/badge/c-0d1117?style=flat-square&logo=c&logoColor=a8b9cc" alt="C">
  <img src="https://img.shields.io/badge/c++-0d1117?style=flat-square&logo=cplusplus&logoColor=f34b7d" alt="C++">
  <img src="https://img.shields.io/badge/c%23-0d1117?style=flat-square&logo=dotnet&logoColor=9b72e8" alt="C#">
  <img src="https://img.shields.io/badge/lua-0d1117?style=flat-square&logo=lua&logoColor=8a94ff" alt="Lua">
  <img src="https://img.shields.io/badge/java-0d1117?style=flat-square&logo=openjdk&logoColor=f89820" alt="Java">
  <img src="https://img.shields.io/badge/javascript-0d1117?style=flat-square&logo=javascript&logoColor=f7df1e" alt="JavaScript">
  <img src="https://img.shields.io/badge/typescript-0d1117?style=flat-square&logo=typescript&logoColor=4f9cf0" alt="TypeScript">
  <img src="https://img.shields.io/badge/html5-0d1117?style=flat-square&logo=html5&logoColor=e34c26" alt="HTML5">
  <img src="https://img.shields.io/badge/css3-0d1117?style=flat-square&logo=css&logoColor=4f9cf0" alt="CSS3">
  <br>
  <img src="https://img.shields.io/badge/vue.js-0d1117?style=flat-square&logo=vuedotjs&logoColor=41b883" alt="Vue.js">
  <img src="https://img.shields.io/badge/vuetify-0d1117?style=flat-square&logo=vuetify&logoColor=4f9cf0" alt="Vuetify">
  <img src="https://img.shields.io/badge/tailwindcss-0d1117?style=flat-square&logo=tailwindcss&logoColor=22d3ee" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/bootstrap-0d1117?style=flat-square&logo=bootstrap&logoColor=8b5cf6" alt="Bootstrap">
  <img src="https://img.shields.io/badge/jquery-0d1117?style=flat-square&logo=jquery&logoColor=4f9cf0" alt="jQuery">
  <img src="https://img.shields.io/badge/mongodb-0d1117?style=flat-square&logo=mongodb&logoColor=47a248" alt="MongoDB">
  <img src="https://img.shields.io/badge/mysql-0d1117?style=flat-square&logo=mysql&logoColor=00a3e0" alt="MySQL">
  <img src="https://img.shields.io/badge/postgres-0d1117?style=flat-square&logo=postgresql&logoColor=6d9fd8" alt="PostgreSQL">
</p>

<sub>The animations are drawn with letters, numbers and symbols by a small Python renderer in <a href="art/">art/</a>, a technique inspired by the ASCII code art of JIN2 (<a href="https://instagram.com/jin_22ee">@jin_22ee</a>).</sub>
