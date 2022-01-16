pragma solidity 0.5.0;

contract Storage {
	string imageHash;
	string perceptual_hash;
	string cryptographic_hash;
	string metaHash;

	//Write Functions(store to blockchain)
	function set(string memory _imageHash, string memory _metaHash, 
	string memory _perceptual_hash, string memory _cryptographic_hash) public {
		imageHash = _imageHash;
		metaHash = _metaHash;
		perceptual_hash = _perceptual_hash;
		cryptographic_hash= _cryptographic_hash;
		
	}

	//Read Function(read from blockchain)
	function getImageHash() public view returns (string memory) {
		return imageHash;
	}
	function getMetaHash() public view returns (string memory) {
		return metaHash;
	}
	function getPerceptual() public view returns (string memory) {
		return perceptual_hash;
	}
	function getCryptographic() public view returns (string memory) {
		return cryptographic_hash;
	}
}