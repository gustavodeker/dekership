var diryJ,dirxJ,jog,velJ,pjx,pjy; // direções,posições,jogador,velocidade..
var velT;
var principal,telaEsq,telaCima,tamTelaW,tamTelaH; // tamanho da tela
var jogo; // status do jogo rodando ou parado
var frames; // controle do loop principal
var contBombas,painelContBombas,velB,tmpCriaBomba;
var bombasTotal;
var vidaPlaneta,barraPlaneta;
var ie,isom;
var telaMsg,telaMsgTxt;
var audio;
var pontos;



function teclaDw(){
    var tecla = event.keyCode;
    if(tecla==38||tecla==87){ // Cima
        diryJ=-1;
    }else if(tecla==40||tecla==83){ // Baixo
        diryJ=1;
    }else if(tecla==37||tecla==65){ // Esquerda
        dirxJ=-1;
    }else if(tecla==39||tecla==68){ // Direita
        dirxJ=1;
    }
    if(tecla==32){ // Espaço - Tiro
        // TIRO
        atira(pjx+17,pjy-5); // 17 e -5 para ajustar a posição do tiro com relação a posição da nave
        //audio.play();
    }
}

function teclaUp(){
    var tecla = event.keyCode;
    if((tecla==38)||(tecla==40)||tecla==87||tecla==83){ // Cima - baixo
        diryJ=0;
    }
    if((tecla==37)||(tecla==39)||tecla==65||tecla==68){ // Esquerda - direita
        dirxJ=0;
    }
    if(tecla==32){ // Espaço - Tiro
        // TIRO
    }
}

function criaBomba(){
    if(jogo){
        var y=telaCima;
        var x=Math.random()*tamTelaW;
        if(x<telaEsq+10){
            x=Math.random()*tamTelaW;
            if(x<telaEsq+10){
                x=Math.random()*tamTelaW;
            }if(x<telaEsq+10){
                x=Math.random()*tamTelaW;
            }if(x<telaEsq+10){
                x=Math.random()*tamTelaW;
            }else{
                x=tamTelaW/2;
            }
        }if(x>tamTelaW-10){
            x=Math.random()*tamTelaW;
            if(x>tamTelaW-10){
                x=Math.random()*tamTelaW;
            }if(x>tamTelaW-10){
                x=Math.random()*tamTelaW;
            }if(x>tamTelaW-10){
                x=Math.random()*tamTelaW;
            }else{
                x=tamTelaW/2;
            }
        }
        var bomba=document.createElement("div");
        var att1=document.createAttribute("class");
        var att2=document.createAttribute("style");
        att1.value="bomba";
        att2.value="top:"+y+"px; left:"+x+"px";
        bomba.setAttributeNode(att1);
        bomba.setAttributeNode(att2);
        document.body.appendChild(bomba);
        contBombas--;
    }
}

function controlaBombas(){
    bombasTotal=document.getElementsByClassName("bomba");
    var principalBack=document.getElementById("omg");
    var tam=bombasTotal.length;
    for(var i=0;i<tam;i++){
        if(bombasTotal[i]){
            var pi=bombasTotal[i].offsetTop; // obtem a posição da bomba
            pi+=velB;
            bombasTotal[i].style.top=pi+"px";
            if(pi>tamTelaH-30){
                vidaPlaneta-=30;

                //principalBack.style.backgroundColor= "white";
                criaExplosao(2,bombasTotal[i].offsetLeft,null);
                bombasTotal[i].remove();
            }
        }
    }
}

function atira(x,y){
    var t=document.createElement("div"); // cria a "bala" dos tiros
    var att1=document.createAttribute("class");
    var att2=document.createAttribute("style");
    att1.value="tiroJog";
    att2.value="top:"+y+"px;"+"left:"+x+"px";
    t.setAttributeNode(att1);
    t.setAttributeNode(att2);
    document.body.appendChild(t);

    document.getElementById("tiro").play();
}

function controleTiros(){
    var tiros=document.getElementsByClassName("tiroJog");
    var tam=tiros.length;
    for(var i=0;i<tam;i++){
        if(tiros[i]){ // se for true/existir
            var pt=tiros[i].offsetTop;
            pt-=velT;
            tiros[i].style.top=pt+"px";
            colisaoTiroBomba(tiros[i]);
            if(pt<telaCima){
                document.body.removeChild(tiros[i]);
                //tiros[i].remove();
            }
        }
    }
}

function colisaoTiroBomba(tiro){
    var tam=bombasTotal.length;
    for(var i=0;i<tam;i++){
        if(bombasTotal[i]){
            if(
                (
                    (tiro.offsetTop<=(bombasTotal[i].offsetTop+70))&& // Cima tiro com baixo da bomba
                    ((tiro.offsetTop+6)>=(bombasTotal[i].offsetTop))  // Baixo do tiro com cima da bomba
                )
                &&
                (
                    (tiro.offsetLeft<=(bombasTotal[i].offsetLeft+20))&& // Esquerda tiro com direita bomba
                    ((tiro.offsetLeft+6)>=(bombasTotal[i].offsetLeft)) // Direita do tiro com esquerda bomba
                )
            ){
                criaExplosao(1, bombasTotal[i].offsetLeft-25,  bombasTotal[i].offsetTop);
                pontos++;
/*PONTUAÇÃO*/   document.getElementById("pontuacao").value = pontos;
                bombasTotal[i].remove();
                tiro.remove();
            }
        }
    }
}

function criaExplosao(tipo,x,y){ // tipo 1=ar tipo 2=terra
    if(document.getElementById("explosao"+(ie-3))){
        document.getElementById("explosao"+(ie-3)).remove();
    }
    //div img e audio
    var explosao=document.createElement("div");
    var img=document.createElement("img");
    var som=document.createElement("audio");
    // atributos para div
    var att1=document.createAttribute("class");
    var att2=document.createAttribute("style");
    var att3=document.createAttribute("id");
    // atributo para imagem
    var att4=document.createAttribute("src");
    // atributos para audio
    var att5=document.createAttribute("src");
    var att6=document.createAttribute("id");

    att3.value="explosao"+ie;

    if(tipo==1){
        att1.value="explosaoAr";
        att2.value="top:"+y+"px;left:"+x+"px;position:absolute;"; // posição da explosão no ar
        att4.value=`imgs/explosao_chao.gif?${new Date()}`; // A mesma do chao pois por enquanto não tem uma melhor
    }else{
        att1.value="explosaoChao";
        att2.value="top:"+(tamTelaH-35)+"px;left:"+(x-30)+"px;position:absolute;"; // posição da explosão no chão
        att4.value=`imgs/explosao_chao.gif?${new Date()}`;
    }
    att5.value=`audio/exp1.wav?${new Date()}`;
    att6.value="som"+isom;
    explosao.setAttributeNode(att1);
    explosao.setAttributeNode(att2);
    explosao.setAttributeNode(att3);
    img.setAttributeNode(att4);
    som.setAttributeNode(att5);
    som.setAttributeNode(att6);
    explosao.appendChild(img);
    explosao.appendChild(som);
    document.body.appendChild(explosao);
    document.getElementById("som"+isom).play();
    
    //document.getElementById("explosao"+ie).remove();
    ie++;
    isom++;
}

function controlaJogador(){
    
    if(pjy<=telaCima+15){
        pjy=telaCima+16;
    }else if(pjy>tamTelaH-25){
        pjy=tamTelaH-26;
    }else{
        pjy+=diryJ*velJ;
    }

    if(pjx<=telaEsq+5){
        pjx=telaEsq+6;
    }else if(pjx>tamTelaW-20){
        pjx=tamTelaW-21;
    }else{
        pjx+=dirxJ*velJ;
    }
    jog.style.top=pjy+"px"; // posicionar o jogador no meio
    jog.style.left=pjx+"px";
}

function gerenciaGame(){
    barraPlaneta.style.width=vidaPlaneta+"px";
    if(contBombas<=0){
        jogo=false;
        clearInterval(tmpCriaBomba);
        telaMsgTxt.innerHTML="VITÓRIA";
        telaMsg.style.display="block";
        
    }
    if(vidaPlaneta<=0){
        jogo=false;
        clearInterval(tmpCriaBomba);
        telaMsgTxt.innerHTML="DERROTA";
        telaMsg.style.display="block";
    }
}

function gameLoop(){
    if(jogo){ // if true
        // funções de controle
        controlaJogador();
        controleTiros();
        controlaBombas();
        atualizaTam();
    }
    gerenciaGame();
    frames=requestAnimationFrame(gameLoop); // gera o loop chamando a função repetidamente
}
function atualizaTam(){
    principal=document.getElementById("omg");  //principal
    telaCima=principal.offsetTop;  // Começo top
    tamTelaH=principal.offsetHeight+principal.offsetTop-30; // Fim baixo
    telaEsq=principal.offsetLeft; // Começo esquerda
    tamTelaW=principal.offsetWidth+principal.offsetLeft-30; // Fim direita
}

function reinicia(){
    bombasTotal=document.getElementsByClassName("bomba");
    var tam=bombasTotal.length;
    for(var i=0;i<tam;i++){
        if(bombasTotal[i]){
            bombasTotal[i].remove();
        }
    }
    telaMsg.style.display="none";
    clearInterval(tmpCriaBomba);
    cancelAnimationFrame(frames);
/**/vidaPlaneta=300;
    pjy=tamTelaH/1.3;
    pjx=tamTelaW/1.8;
    jog.style.top=pjy+"px";
    jog.style.left=pjx+"px";
    contBombas=1000;
/**/pontos=0;
    document.getElementById("pontuacao").innerHTML="";
    jogo=true;
    if(principal.offsetWidth<800){ 
////////MODO HARD//////////////////        
        tmpCriaBomba=setInterval(criaBomba,1300);
    } else{
        tmpCriaBomba=setInterval(criaBomba,2000);
    }

    gameLoop();
}

function inicia(){
    jogo=false;
/**/pontos=0;

    // Inicialização da tela
    principal=document.getElementById("omg");  //principal
    telaCima=principal.offsetTop;  // Começo top
    tamTelaH=principal.offsetHeight+principal.offsetTop-30; // Fim baixo
    telaEsq=principal.offsetLeft; // Começo esquerda
    tamTelaW=principal.offsetWidth+principal.offsetLeft-30; // Fim direita
    /*document.write(telaCima+"<br>");
    document.write(tamTelaH+"<br>");
    document.write(telaEsq+"<br>");
    document.write(tamTelaW+"<br>");*/


    // Iniciali zação do jogador
    dirxJ=diryJ=0;
    pjy=tamTelaH/1.3; // dividindo tamanho da tela por 2 para achar o meio
    pjx=tamTelaW/1.8; //
    velJ=7;
    velT=6;
    jog=document.getElementById("naveJog");
    jog.style.top=pjy+"px"; // posicionar o jogador no meio
    jog.style.left=pjx+"px";
    
    // Controle das bombas
    contBombas=5;
    velB=2;

////////MODO HARD//////////////////
    if(principal.offsetWidth<800){ 
        velB=3;
    }

    // Controle explosão
    ie = 0;
    isom = 0;

    // Controle do planeta
    //vidaPlaneta=300;
    barraPlaneta=document.getElementById("barraPlaneta");
    barraPlaneta.style.width=vidaPlaneta+"px";

    // Telas
    telaMsg=document.getElementById("telaMsg");
    telaMsgTxt=document.getElementById("telaMsgTxt");
    telaMsg.style.display="block";
    telaMsgTxt.innerHTML="WELLCOME";
    document.getElementById("btnJogar").addEventListener("click",reinicia);

   // audio=document.getElementById('audio');
}

window.addEventListener("load",inicia);
document.addEventListener("keydown",teclaDw);
document.addEventListener("keyup",teclaUp);
