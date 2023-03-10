Foxy-Farmer
======

Foxy-Farmer is a simplified farmer for the chia blockchain using the Foxy-Pool chia farming gateway to farm without a full node running on your machine.
NFT and OG pooling are both supported!

> **Note**:
> If you can run a full node, you should!

Foxy-Farmer is useful in the following scenarios:
- You are replotting your OG pooling farm to compressed madmax NFT plots but do not want to run two full nodes
- Your hardware does not support running a full node

## Installing

### Using the binary

1. Download the latest binary zip for your OS from the [releases page](https://github.com/foxypool/foxy-farmer/releases/latest)
2. Run the binary, it will create a default `foxy-farmer.yaml` in the current directory based on your current chia `config.yaml`
3. Edit the `foxy-farmer.yaml` to your liking and restart foxy-farmer
4. Profit!

### Running from source

1. Clone the git repo and cd into it: `git clone https://github.com/foxypool/foxy-farmer && cd foxy-farmer`
2. Install the dependencies: `pip install .`
3. Run using `foxy-farmer`, it will create a default `foxy-farmer.yaml` in the current directory based on your current chia `config.yaml`
4. Edit the `foxy-farmer.yaml` to your liking and restart foxy-farmer
5. Profit!

### Using docker

A docker image based on the provided [Dockerfile](https://github.com/foxypool/foxy-farmer/blob/main/Dockerfile) is available via `ghcr.io/foxypool/foxy-farmer:latest`.
For specific tags see [this list](https://github.com/foxypool/foxy-farmer/pkgs/container/foxy-farmer).
A [docker-compose.yaml](https://github.com/foxypool/foxy-farmer/blob/main/docker-compose.yaml) example is available as well, to get started.

Currently, this requires you to have a working `foxy-farmer.yaml` already available to mount into the container. See this [example configuration](https://docs.foxypool.io/proof-of-spacetime/foxy-farmer/configuration/#example-configuration) for reference.

## Are my keys safe?

Yes, Foxy-Farmer itself is open source and uses the [og pooling patched chia-blockchain client](https://github.com/foxypool/chia-blockchain) under the hood which is open source as well, so you can verify yourself nothing funky happens. As such the farming topology has not changed, your locally running farmer still signs your blocks, same as when running a local full node. Your keys do not leave your machine.

## Can i use the Foxy-Pool chia farming gateway without pooling in Foxy-Pool?

Yes, using the chia farming gateway without pooling in Foxy-Pool is supported, but a 1% fee is charged when farming a block with a Pool Public Key or Launcher Id which is not pooling with Foxy-Pool.

## Using remote harvesters

You can use remote harvesters with foxy-farmer, just make sure to use the port 18447 and use the ssl ca directory from `.foxy-farmer`.
A `make_harvester_installer.ps1` and `run_harvester.ps1` script is provided to simplify this for Windows users, especially when running gigahorse remote harvesters already. Just run the `make_harvester_installer.ps1` script and copy the resulting `foxy-harvester` directory onto the remote harvesters and run `run_harvester.ps1` on them.

## License

GNU GPLv3 (see [LICENSE](https://github.com/foxypool/foxy-farmer/blob/main/LICENSE))
