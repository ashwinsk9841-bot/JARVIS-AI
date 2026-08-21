document.addEventListener("mousemove",(e)=>{

const pupils=document.querySelectorAll(".pupil");

pupils.forEach((pupil)=>{

const eye=pupil.parentElement;

const rect=eye.getBoundingClientRect();

const eyeX=rect.left+rect.width/2;
const eyeY=rect.top+rect.height/2;

const angle=Math.atan2(e.clientY-eyeY,e.clientX-eyeX);

const x=Math.cos(angle)*15;
const y=Math.sin(angle)*15;

pupil.style.transform=`translate(${x}px,${y}px)`;

});

});