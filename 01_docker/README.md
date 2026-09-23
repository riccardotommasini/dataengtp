# Wordsmith Docker Exercises

This repository contains a small multi-service application used to explore
Docker, Docker Compose, and Docker Model Runner through hands-on exercises.

It was originally developped by Jerome Petazzoni [original](https://github.com/jpetazzo/wordsmith)

The project currently includes:

- `web`: the original Go frontend
- `web2`: a Node.js evolution of the frontend with newer UI interactions
- `words`: a Java API serving generated words
- `db`: a PostgreSQL database storing the word lists and generated stories
- `narrative`: a Python API that calls `words` and a model server to generate short stories

The repository is designed as a learning playground for:

- writing Dockerfiles
- connecting services with Docker Compose
- exposing ports and volumes
- integrating Docker Model Runner into an application stack
- extending the application with new services

Documentation:

- [English guide](README.en.md)
- [Guide en français](README.fr.md)

## Install Docker

Before starting the exercises, make sure Docker and Docker Compose are available
on your machine.

Recommended setup:

- macOS: install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Windows: install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and enable WSL2 integration
- Linux: install Docker Engine and the Docker Compose plugin from your distribution packages or from the [official Docker docs](https://docs.docker.com/engine/install/)

Quick check:

```bash
docker --version
docker compose version
```

If you want to use the LLM features in this repository, also make sure Docker Model Runner is available in your Docker installation.

## Get Ready For Class

This repository includes helper scripts that pre-pull the required base images
and model so students can start the exercises faster.

For macOS and Linux:

```bash
./get-ready-for-class
```

For Windows PowerShell:

```powershell
.\get-ready-for-class.ps1
```

Both scripts:

- check Docker, Docker Compose, and Docker Model Runner
- ask which Docker platform should be used
- set `DOCKER_DEFAULT_PLATFORM` for the script session
- pull the required container images
- pull the required model
- print a success banner when everything is ready

## Note For Windows Users

If you use Docker Desktop with WSL2, it can be useful to create a `.wslconfig`
file in your Windows user profile directory and add the following content:

```
[wsl2]
# Cap the total RAM WSL2 can use across all distros.
# On an 8 GB machine, 4 GB is a safe ceiling for Docker work.
memory=4GB

# Limit vCPUs WSL2 can use (optional).
# If you have a 4-core/8-thread CPU, 4 here is reasonable.
processors=4

# Provide swap space for memory spikes (Docker builds, etc.).
# Keep this modest on an 8 GB host.
swap=4GB

# Optional: store the swap file somewhere with enough free space.
# Comment this out to use the default location.
# swapfile=C:\\wsl-swap.vhdx

# Keep localhost port forwarding (Windows <-> Linux) enabled.
localhostForwarding=true

```

Then restart Docker Desktop.
