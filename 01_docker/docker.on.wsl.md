## For Windows Users users

1) Change operating systems

2) if you cannot do that
3) create a file .wslconfig in the folder /Users/<UserProfile>
4) copy the following content in it
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
5) reboot docker
