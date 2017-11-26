# Content Blockchain GUI Prototype

A proof of concept GUI Application for the 
[Content Blockchain](https://content-blockchain.org).

The **Content Blockchain Project** is building the foundational tools that 
enable journalists, publishers, and media start-ups to create new innovative 
products, services and business models in the open blockchain economy.

This software allows you to run a full content blockchain node on your and 
participate in testing the plattform. It allows you to:

- run your own blockchain-node (testnet)
- create an account on the blockchain
- test the experimental voting based consensus
- send and receive native blockchain coins
- timestamp content on the blockchain

An installable version is currently available for 64-Bit Windows.
You can download it [here](https://github.com/coblo/gui-demo/releases/download/v0.2.1/Coblo-0.2.1-win.msi).
If you need help or have questions you can reach us via telegram:
[https://t.me/ContentBlockchainBeta](https://t.me/ContentBlockchainBeta)

Please report any issues at [https://github.com/coblo/gui-demo/issues](https://github.com/coblo/gui-demo/issues)

## Overview

<img align="left" width="150" src="docs/screenshot_wallet.jpg?raw=true">

### Wallet

Content is registered via transactions that are replicated and stored on the
blockchain. Infrastructure providers are rewarded with tokens for their 
services. The wallet screen shows your token balance and transaction history.
You may exchange tokens with other participants.

<img align="left" width="150" src="docs/screenshot_timestamp.jpg?raw=true">

### Timestamping

A minimal demonstration of content timestamping. Here you can create, search
and optionally register a unique fingerprint (SHA256 hash) of any document or
file. This will be extended to demonstrate content registration with 
[ISCC codes](http://iscc.codes/ "International Standard Content Code")


<img align="left" width="150" src="docs/screenshot_community.jpg?raw=true">

### Community 

Demonstration of a decentralized voting based governance. Participants that 
operate full  nodes on the network can become **Validators** and earn tokens
for their services. **Guardians** determine **Validators** by on-chain voting.

## Credits

The Content Blockchain Project received funding from the 
[Google Digital News Initiative](https://digitalnewsinitiative.com/dni-projects/content-blockchain-project/).

This application was build with [Python](https://www.python.org/), 
[PyQT](https://riverbankcomputing.com/software/pyqt/intro),
[MultiChain](https://www.multichain.com/), and many other open source libraries and tools.
Our thanks go out to the entire open source community.
