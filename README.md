<div align="center">

<img src="assets/hero.gif" alt="YOLOOO, rendered as animated ASCII in JetBrains Mono: the name ignites under a scan beam, holds, then burns off into embers" width="100%">

</div>

---

<div align="center">

Student @ ACS, Politehnica Bucuresti

</div>

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
