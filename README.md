# Content Blockchain GUI Prototype

**OLD TESTNET 1 BACKUP BRANCH**

A proof of concept GUI Application for the 
[Content Blockchain](https://content-blockchain.org).

The **Content Blockchain Project** is building the foundational tools that 
enable journalists, publishers, and media start-ups to create new innovative 
products, services and business models in the open blockchain economy.

This software allows you to run a full content blockchain node on your computer
and participate in testing the plattform. It allows you to:

- run your own blockchain-node (testnet)
- create an account on the blockchain
- test the experimental voting based consensus
- send and receive native blockchain coins
- timestamp content on the blockchain

An installable version is currently available for 64-Bit Windows.
You can download it [here](https://github.com/coblo/gui-demo/releases/download/v0.2.1/Coblo-0.2.1-win.msi).
If you need help or have questions you can reach us via Telegram:
[https://t.me/ContentBlockchainBeta](https://t.me/ContentBlockchainBeta)

Please report any issues at [https://github.com/coblo/gui-demo/issues](https://github.com/coblo/gui-demo/issues)

## Overview

<img align="left" width="150" src="docs/screenshot_wallet.jpg?raw=true">

**Wallet**

Content is registered via transactions that are replicated and stored on the
blockchain. Infrastructure providers are rewarded with tokens for their 
services. The wallet screen shows your token balance and transaction history.
You may exchange tokens with other participants.

<img align="left" width="150" src="docs/screenshot_timestamp.jpg?raw=true">

**Timestamping**

A minimal demonstration of content timestamping. Here you can create, search
and optionally register a unique fingerprint (SHA256 hash) of any document or
file. This will be extended to demonstrate content registration with 
[ISCC codes](http://iscc.codes/ "International Standard Content Code")


<img align="left" width="150" src="docs/screenshot_community.jpg?raw=true">

**Community** 

Demonstration of a decentralized voting based governance. Participants that 
operate full  nodes on the network can become **Validators** and earn tokens
for their services. **Guardians** determine **Validators** by on-chain voting.


## Development Setup

If you want to contribute or just play around with the code you will need
**Python 3.5** on your system. The application is cross platform and should
generally work on any 64-Bit Linux, Mac or Windows. Please be aware that this
is a "Proof of Concept" and the code is not meant to be production grade. 
These are the steps to get your hands dirty:

- Checkout this repository to you machine
- Optionaly create a virtual environment for the project
- Install python dependencies with `pip install -r requirements.txt`
- Download [multichaind binaries](https://www.multichain.com/download-install/) and place them in `/app/bin`
- Compile QT .ui files with `comile_ui.py`

Now you should be able to run `main.py`. Launching the application will check
if you have a `profile.db` SQLite file in your systems app data folder.
For example on Windows that would be `C:\Users\YOURUSERNAME\AppData\Local\Content-Blockchain\Coblo\profile.db`.
If that file does not exist the application will guide you through the setup wizard
to create a `profile.db` and a blockchain address.

By default the application will manage the `multichaind` node proccess.
For development you might want to manage the process yourself.
See `runchain.example.bat` for how to manually start a MultiChain node on Windows.
The first time setup wizard also allows to specify connection data for you
manually managed node.

By installing the `requirements-dev.txt` dependencies you will also be able to
create frozen app builds and edit .ui files with QT-Designer. The Windows
build/dist is created with `python setup.py bdist_msi`. `pyqt5-tools` will
install the QT-Designer executable to your python `site-packages/pyqt5-tools`
folder.


## Credits

The Content Blockchain Project received funding from the 
[Google Digital News Initiative](https://digitalnewsinitiative.com/dni-projects/content-blockchain-project/).

This application was build with [Python](https://www.python.org/), 
[PyQT](https://riverbankcomputing.com/software/pyqt/intro),
[MultiChain](https://www.multichain.com/), and many other open source libraries and tools.
Our thanks go out to the entire open source community.
