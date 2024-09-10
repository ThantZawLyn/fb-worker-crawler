const proxyChain = require('proxy-chain');
const express = require("express");
const app = express();
const port = 3000;

app.get("/", (request, response) => {
  response.send(`Proxy server management service works`);
});

app.get("/open/:proxy", async (request, response) => {
  try {
    console.log('opening proxy: ' + request.params["proxy"]);
    const oldProxyUrl = 'http://' + request.params["proxy"];
    const newProxy = await proxyChain.anonymizeProxy(oldProxyUrl);
    response.send({url: newProxy});
  }
  catch (e) {
    console.log(e)
    response.send({message: 'error: ' + e.message});
  }
});

app.get("/close/:proxy", async function(request, response){
  let proxy = request.params["proxy"];
  let result = await proxyChain.closeAnonymizedProxy('http://' + proxy, true);
  response.send({message: "close proxy " + proxy + " result: " + result});
});

app.listen(port);
console.log("Proxy server started");
