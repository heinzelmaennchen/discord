const Discord = require('discord.js');
const client = new Discord.Client();

client.on('ready', () => {
    console.log('I am ready!');
});

client.on('message', message => {
    if (message.content === 'ping') {
    	message.reply('pong');
  	}
    if (message.content === 'seas') {
    	message.reply('seas!11');
  	}
  	if (message.content === '$BTC') {
       console.log('received BTC command');
       //let price = getCoinPrice('BTC');
       getCoinPrice('BTC');
       message.reply('request received, output in console');
  	}
});

function reqListener () {
  console.log(this.responseText);
}


function getCoinPrice(coinTicker) {
  let url = 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms='+ coinTicker +'&tsyms=EUR';
  console.log(url);
  
  let oReq = new XMLHttpRequest();
  oReq.addEventListener("load", reqListener);
  oReq.open("GET", url);
  oReq.send();

  //let result = UrlFetchApp.fetch(url);
  //let data = JSON.parse(result.getContentText());
  //console.log(data);
  //let coinData = data.RAW[coinTickers[ticker]].EUR;
  //console.log(coinData);
  //let price = coinData.PRICE;
  //let dailyLow = coinData.LOW24HOUR;
  //let dailyHigh = coinData.HIGH24HOUR;
  //let pctChange = coinData.CHANGEPCT24HOUR;

  //return price;
}

// THIS  MUST  BE  THIS  WAY
client.login(process.env.BOT_TOKEN);
