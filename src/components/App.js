import React, {Component } from 'react';
import Web3 from 'web3';
import './App.css';
import Storage from '../abis/Storage.json'
import { create } from 'ipfs-http-client'
import axios from "axios";

// or using options
const ipfs = create({ host: 'ipfs.infura.io', port: '5001', protocol: 'http' })


const url = "http://localhost:5000/test";

var imgpath='hkbj'
var metapath=''
var timestamp =''
var perceptual_hash=''
var cryptographic_hash=''
var isOriginal
var blocks = []
class App extends Component {

  async componentWillMount() {
    console.log("loading")
    await this.loadWeb3()
    await this.loadBlockchainData()
  }



  async loadBlockchainData() {
    const web3 = window.web3
    
    //get latest block number
    let block = await web3.eth.getBlock("latest")
    let n=block.number
    //iterate through blocks to get transaction input and contract address for decoding
    for(let i=1;i<=n ;++i)
    {
        let transaction =await web3.eth.getTransactionFromBlock(i, 0)
        if(transaction!=null ){
        let blockObj = {hash: transaction['to'] , input:transaction['input'] }
        blocks.push(blockObj)}
    }
    // Load account
    const accounts = await web3.eth.getAccounts()
    this.setState({account: accounts[0]})
    const networkId= await web3.eth.net.getId()
    const networkData = Storage.networks[networkId]
    
    if(networkData){
      const abi = Storage.abi
      const address = networkData.address
      const contract = new web3.eth.Contract(abi, address)
      this.setState({contract})
      const imageHash = await contract.methods.getImageHash().call()
      const metaHash = await contract.methods.getMetaHash().call()
      const perceptual_hash= await contract.methods.getPerceptual().call()
      const cryptographic_hash = await contract.methods.getCryptographic().call()
      this.setState({imageHash})
      this.setState({metaHash})
      this.setState({perceptual_hash})
      this.setState({cryptographic_hash})
    } else {
      window.alert('Smart contract not deployed to detected network')
    }
    
  }

  constructor(props) {
    super(props);
    this.state = {
      account: '',
      buffer: null,
      buffer1: null,
      contract: null,
      imageHash: '',
      metaHash:'',
      perceptual_hash: '',
      cryptographic_hash: '',
      copyright_path:''
    };
    this.captureFile=this.captureFile.bind(this)
  }


  async loadWeb3() {
    if (window.ethereum) {
      window.web3 = new Web3(window.ethereum)
      await window.ethereum.enable()
    }
    else if (window.web3) {
      window.web3 = new Web3(window.web3.currentProvider)
    }
    else {
      window.alert('Please install Metamask!')
    }
  }

  
  //capture path of image
 captureImage = (event) => {
    event.preventDefault()
    console.log('image file captured..')
    imgpath=event.target.value
 }  

 //capture pathofcopyright information
 captureMeta = (event) => {
    event.preventDefault()
    console.log('copyright file captured..')
    metapath=event.target.value
 }  


 captureFile = (event) => {
    event.preventDefault()
    var base = ''
    var metabase = ''
    var copyright_path=''
    var image_path=''
    console.log(imgpath)
    console.log(metapath)
    //post imagepath, metapath, and blocks info to flask
    axios({
            method: 'post',
            url: url,
            data: {
                imgPath: imgpath,
                metaPath: metapath,
                blocks: blocks           }
        })
        .then(function (response) {
          //get response from flask
          console.log(response.data)
        base=response.data['watermarked']
        metabase=response.data['copyright']
        perceptual_hash=response.data['perceptual_hash']
        cryptographic_hash=response.data['cryptographic_hash']
        isOriginal = response.data['Original']
        copyright_path=response.data['original_copyright']['_metaHash']
        image_path=response.data['original_copyright']['_imageHash']

        })
        .catch(function (error) {
        console.log(error);
  }).then(() => {
    // convert base64 image and copyrigth info to buffer if the uploaded image is original

    if(isOriginal==true){
      base = base.substring(2)
      metabase=metabase.substring(2)
      base = base.substring(0,base.length-1)
      metabase = metabase.substring(0,metabase.length-1)
      base='data:image/png;base64,'+base
      metabase='data:text/plain;base64,'+metabase
      var arr = base.split(','),
            mime = arr[0].match(/:(.*?);/)[1],
            bstr = window.atob(arr[1]), 
            n = bstr.length, 
            u8arr = new Uint8Array(n);

            while(n--){
            u8arr[n] = bstr.charCodeAt(n);
        }
  var file =  new File([u8arr], 'test.png', {type:mime})
  const reader = new window.FileReader()
    reader.readAsArrayBuffer(file)
    reader.onloadend = () => {
      this.setState({buffer:Buffer(reader.result)})
      console.log(this.state.buffer)
    }
    /////////////////////////
    var arr = metabase.split(','),
            mime = arr[0].match(/:(.*?);/)[1],
            bstr = window.atob(arr[1]), 
            n = bstr.length, 
            u8arr = new Uint8Array(n);

            
        while(n--){
            u8arr[n] = bstr.charCodeAt(n);
        }
    file =new File([u8arr], 'test.png', {type:mime})
    const reader1 = new window.FileReader()
    reader1.readAsArrayBuffer(file)
    reader1.onloadend = () => {
      this.setState({buffer1:Buffer(reader1.result)})
      console.log(this.state.buffer1)
    }


    ////////////////////////
    alert("Congratulations!Your image is original. Please, proceed with the transaction to publish it on secure network.")
  }
  if(isOriginal==false)
  {
    //show copyright info of original image

    if (window.confirm('Your Image cannot be uploaded on IPFS as its copyright has already been claimed! The IPFS path of existing image is: \ni"https://ipfs.infura.io/ipfs/'+image_path+'"\n Click ok to see its copyright.')) 
    {
      window.location.href=`https://ipfs.infura.io/ipfs/${copyright_path}`;
    };
  }

});
  
}


 //Example hash: "QmaEcpNenJGJMpxEGFTPE1ft7jVfii3PZQsmYs2GLjdffR"


 //Example url: https://ipfs.infura.io/ipfs/QmbFMke1KXqnYyBBWxB74N4c5SBnJMVAiMNRcGu6x1AwQH

 onSubmit = async(event) => {
    event.preventDefault()
    console.log("Submitting the form...")

    //add image and meta file to ipfs
    const file =await ipfs.add(this.state.buffer)
    console.log("image file ipfs_hash")
    console.log(file)
    const imageHash=file.path
    const metafile = await ipfs.add(this.state.buffer1)
    console.log("copyright info ipfs_hash")
    console.log(metafile)
    const metaHash =metafile.path
  
    //Step 2: store informations on blockchain
  
    this.state.contract.methods.set(imageHash, metaHash, perceptual_hash, cryptographic_hash)
    .send({from: this.state.account})
    .then((r) => {
      this.setState({imageHash})
      this.setState({metaHash})
      this.setState({perceptual_hash})
      this.setState({cryptographic_hash})
      console.log("hash set")
    })
    

  }


 render() {

    return (
      <div>
        <nav className="navbar navbar-dark fixed-top bg-dark flex-md-nowrap p-0 shadow">
          <a className="navbar-brand col-sm-3 col-md-2 mr-0"
            target="_blank"
            rel="noopener noreferrer"
          >
            BTech Project
          </a>
          <ul className="navbar-nav px-3">
          <li className="nav-item text-nowrap d-none d-sm-none d-sm-block">
          <small className="text-white"> {this.state.account}</small>
          </li>
          </ul>
        </nav>

      <div className="split right">
      <div className="centered">
      <img className="image-container" src = {`https://ipfs.infura.io/ipfs/${this.state.imageHash}`} />
      <p>&nbsp;</p>
      <form action={`https://ipfs.infura.io/ipfs/${this.state.imageHash}`}>
    <input type="submit" target="_blank " value="View Image on IPFS" />
      </form>

         <p>&nbsp;</p>

      <form action={`https://ipfs.infura.io/ipfs/${this.state.metaHash}`}>
    <input type="submit" target="_blank " value="View Copyright on IPFS" />
      </form>
      
      </div> 
      </div>
        <div className= "split left">
        <div className="centered">
          <div className="row">
            <main role="main" className="col-lg-12 d-flex text-center">

              <div className = "inputs">
                
                <label>Image Path</label>
                <form>
                <input type='text' onChange={this.captureImage}/>
                
                </form>

                <label> Copyright Info Path</label>
                <form>
                <input type='text' onChange={this.captureMeta}/>
                </form>
                <p>&nbsp;</p>
                <form onSubmit={this.captureFile}>

                <input className = "submit-button" name='Confirm' type= 'submit' value='Confirm Input'/>
                </form>
                
                <form onSubmit={this.onSubmit}>
                <input className = "submit-button"  name='Submit' type= 'submit' value='Upload on IPFS'/>
                </form>
               <p>&nbsp;</p>
              </div>
            </main>
          </div>
          </div>
        </div>
       
      </div>
    );
  }
}

export default App;