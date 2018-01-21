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
       let price = getCoinPrice('BTC');
       message.reply('BTC price: ' + price + 'EUR');
  	}
});

function getCoinPrice(coinTicker) {
  let url = 'https://min-api.cryptocompare.com/data/pricemultifull?fsyms='+ coinTicker +'&tsyms=EUR';
  let result = UrlFetchApp.fetch(url);
  let data = JSON.parse(result.getContentText());
  let coinData = data.RAW[coinTickers[ticker]].EUR;
  let price = coinData.PRICE;
  let dailyLow = coinData.LOW24HOUR;
  let dailyHigh = coinData.HIGH24HOUR;
  let pctChange = coinData.CHANGEPCT24HOUR;

  return price;
}

// THIS  MUST  BE  THIS  WAY
client.login(process.env.BOT_TOKEN);
