Foxy-Farmer
======

Foxy-Farmer is a simplified farmer for the chia blockchain using the Foxy-Pool chia farming gateway to farm without a full node running on your machine.

- [x] NFT and OG pooling are both supported!
- [x] Bladebit compressed plots are supported!

> **Note**:
> If you can run a full node, you should!

Foxy-Farmer is useful in the following scenarios:
- You are replotting your OG pooling farm to compressed madmax NFT plots but do not want to run two full nodes
- Your hardware does not support running a full node

If you are migrating from FlexFarmer please check out [this guide](https://docs.foxypool.io/proof-of-spacetime/guides/switching-from-flex-farmer-to-foxy/).

The docs can be found [here](https://docs.foxypool.io/proof-of-spacetime/foxy-farmer/). 

## Installing

### Using the binary

1. Download the latest binary zip for your OS from the [releases page](https://github.com/foxypool/foxy-farmer/releases/latest)
2. Run the binary, it will create a default `foxy-farmer.yaml` in the current directory based on your current chia `config.yaml`
    > **Note**:
    > If you never set up chia before on this machine you will need to import your 24 word mnemonic using `./foxy-farmer keys add` and ensure the `config.yaml` in `<USER_HOME>/.foxy-farmer/mainnet/config/` includes your PlotNFT in the pool list. This can be achieved by manually copying it from another `config.yaml` or running `./foxy-farmer join-pool`.

3. Edit the `foxy-farmer.yaml` to your liking and restart foxy-farmer
4. Profit!

### Running from source

1. Clone the git repo and cd into it: `git clone https://github.com/foxypool/foxy-farmer && cd foxy-farmer`
2. Create a venv:
    ```bash
    python3 -m venv venv
    ```
3. Install the dependencies:
    ```bash
    venv/bin/pip install .
    ```
4. Run using `venv/bin/foxy-farmer` (or activate the venv using `source venv/bin/activate` and then just use `foxy-farmer`), it will create a default `foxy-farmer.yaml` in the current directory based on your current chia `config.yaml` if available.
   > **Note**:
   > If you never set up chia before on this machine you will need to import your 24 word mnemonic using `venv/bin/foxy-farmer keys add` and ensure the `config.yaml` in `<USER_HOME>/.foxy-farmer/mainnet/config/` includes your PlotNFT in the pool list. This can be achieved by manually copying it from another `config.yaml` or running `venv/bin/foxy-farmer join-pool`.

5. Edit the `foxy-farmer.yaml` to your liking and restart foxy-farmer
6. Profit!

### Using docker

A docker image based on the provided [Dockerfile](https://github.com/foxypool/foxy-farmer/blob/main/Dockerfile) is available via `ghcr.io/foxypool/foxy-farmer:latest` and `foxypool/foxy-farmer:latest`.
For specific tags see [this list](https://github.com/foxypool/foxy-farmer/pkgs/container/foxy-farmer).
A [docker-compose.yaml](https://github.com/foxypool/foxy-farmer/blob/main/docker-compose.yaml) example is available as well, to get started.

Currently, this requires you to have a working `foxy-farmer.yaml` already available to mount into the container. See this [example configuration](https://docs.foxypool.io/proof-of-spacetime/foxy-farmer/configuration/#example-configuration) for reference.
If you do not have a `.chia_keys` directory from a previous chia install, you can set the `CHIA_MNEMONIC` environment variable to your 24 words and it will create they keyring accordingly. Please unset it again once done.

> **Note**:
> To execute the `join-pool` command please first shutdown foxy-farmer using `docker compose down` and then run `docker compose run farmer foxy-farmer join-pool`.

## Updating

### Using the binary

Just download the latest version of the binary [from here](https://github.com/foxypool/foxy-farmer/releases/latest) like you did on install and replace the existing binary, that's it.

### Running from source

1. Open a terminal in the `foxy-farmer` directory which you cloned during install.
2. Run `git pull`
3. Run `venv/bin/pip install --upgrade .`

### Using docker

Pull the latest image using `docker pull ghcr.io/foxypool/foxy-farmer:latest` and recreate the container using `docker compose up -d`.

## Are my keys safe?

Yes, Foxy-Farmer itself is open source and uses the [og pooling patched chia-blockchain client](https://github.com/foxypool/chia-blockchain) under the hood which is open source as well, so you can verify yourself nothing funky happens. As such the farming topology has not changed, your locally running farmer still signs your blocks, same as when running a local full node. Your keys do not leave your machine.

## Can i use the Foxy-Pool chia farming gateway without pooling in Foxy-Pool?

Yes, using the chia farming gateway without pooling in Foxy-Pool is supported, but a 1% fee is charged when farming a block with a Pool Public Key or Launcher Id which is not pooling with Foxy-Pool.

## Using remote harvesters

You can use remote harvesters with foxy-farmer, just make sure to use the port 18447 and use the ssl ca directory from `.foxy-farmer`.
A `make_harvester_installer.ps1` and `run_harvester.ps1` script is provided to simplify this for Windows users, especially when running gigahorse remote harvesters already. Just run the `make_harvester_installer.ps1` script and copy the resulting `foxy-harvester` directory onto the remote harvesters and run `run_harvester.ps1` on them.

## License

GNU GPLv3 (see [LICENSE](https://github.com/foxypool/foxy-farmer/blob/main/LICENSE))
