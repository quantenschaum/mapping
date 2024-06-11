function d2dm(a,n=1,l=3){
    var deg = (new URL(document.location)).searchParams.get("deg");
    if(deg) {
        var n=parseInt(deg);
        var f=Math.pow(10,n);
        return Math.round(a*f)/f;
    }
    var a=Math.abs(a);
    var d=Math.floor(a);
    d=("0000"+d).slice(-l);
    var f=Math.pow(10,n);
    var m=Math.round(((60*a)%60)*f)/f;
    while(m>=60) { m-=60; d+=1; }
    var M=m==0?"":m.toFixed(n).replace(/\.?0+$/,"")+"'";
    return d+'°'+M;
}

function center(a,b,m=0.5) {
  var x=a.lat*(1-m)+b.lat*m;
  var y=a.lng*(1-m)+b.lng*m;
  return L.latLng(x,y);
}

function distance(a,b) {
  return a.distanceTo(b)/1852;
}

function degrees(a) { return a*180/Math.PI; }
function radians(a) { return a*Math.PI/180; }
function sin(a) { return Math.sin(radians(a)); }
function cos(a) { return Math.cos(radians(a)); }
function atan2(x,y) { return degrees(Math.atan2(x,y)); }

function bearing(a,b) {
  var x = cos(b.lat)*sin(b.lng-a.lng);
  var y = cos(a.lat)*sin(b.lat)-sin(a.lat)*cos(b.lat)*cos(b.lng-a.lng);
  return (360+atan2(x,y))%360;
}

function position(ll) {
  var x=ll.lng;
  var y=ll.lat;
  return `${y>0?'N':'S'}&nbsp;${d2dm(y,3,2)}<br/>${x>0?'E':'W'}&nbsp;${d2dm(x,3,3)}`;
}

L.ChartTools = L.Layer.extend({
  initialize: function(options) {

    options = Object.assign({
      urlPrefix:''
    }, options);

    var urlPrefix = options.urlPrefix;

    L.Util.setOptions(this, options);

    L.Control.ChartToolButton = L.Control.extend({
      initialize: function(options) {
        if(!('position' in options)) {
          options.position='topleft';
        }
        L.Util.setOptions(this, options);
      },
      onAdd: function(map) {
          var img = L.DomUtil.create('img','charttools-button');
          img.src = urlPrefix+this.options.iconUrl;
          if ('title' in this.options) {
            img.title = this.options.title;
          }
          if ('click' in this.options) {
            L.DomEvent.on(img, 'click', e => this.options.click(e));
            L.DomEvent.disableClickPropagation(img);
          }
          return img;
      },
    });

    L.Control.ChartToolInfo = L.Control.extend({
      initialize: function(options) {
        if(!('position' in options)) {
          options.position='bottomleft';
        }
        L.Util.setOptions(this, options);
      },
      onAdd: function(map) {
          var div = L.DomUtil.create('div','charttools-info');
          this._div=div;
          return div;
      },
      setText: function(text) {
        this._div.innerHTML=text;
      }
    });

  },

  onAdd: function(map) {
    this._map = map;
    var g=this._layerGroup=L.featureGroup().addTo(map);

    function cursor(style,element=document.getElementById('map')) {
      element.style.cursor=style;
    }

    var options = this.options;

    var storage=sessionStorage;

    function Marker(ll,icon,text,id) {
      var marker=L.marker(ll, {
        icon: L.icon({
            iconUrl: options.urlPrefix+icon,
            iconSize: [40,40],
        })
      }).addTo(g);
      var today = new Date();
      var h = ('0'+today.getHours()).slice(-2);
      var m = ('0'+today.getMinutes()).slice(-2);
      var label=L.marker(ll, {
        icon: L.divIcon({
            html: text ? text : `${h}:${m}`, //moment().format("HH:mm"),
            className: "charttools-label",
            iconAnchor: [-10,-10],
        })
      }).addTo(g);
      var storageID=id||'marker-'+Math.floor(Math.random()*1e8);
      marker.store=function(){
        storage.setItem(storageID,JSON.stringify({
          ll:[marker.getLatLng().lat,marker.getLatLng().lng],
          icon:icon,
          text:label._icon.innerHTML,
        }));
      }
      marker.store();
      marker.on('move', e => {
        label.setLatLng(e.latlng);
//        marker.bindTooltip(position(e.latlng));
        marker.store();
      });
      marker.on('contextmenu', e => {
        label.remove();
        marker.remove();
        storage.removeItem(storageID);
      });
      return marker;
    }

//    storage.clear();
    for (let i = 0; i < storage.length; i++) {
      let k=storage.key(i);
      let v=storage.getItem(k);
      if(k.startsWith('marker')){
        v=JSON.parse(v);
        Marker(v.ll,v.icon,v.text,k);
      }
    }

    function addMarkerControl(icon, title, text=null) {
      new L.Control.ChartToolButton({
        iconUrl: icon,
        title: title,
        click: e => {
          var marker=Marker([0,0],icon,text);
          cursor("none",marker._icon);
          map.on('click mousemove', me => {
            marker.setLatLng(me.latlng);
            if(me.type=="click"){
              map.off('click mousemove');
              marker.bindTooltip(position(me.latlng));
              cursor("auto",marker._icon);
            }
          });
        }
      }).addTo(map);
    }

    function addLineControl(icon, title, bear=0, dashed=false, m=1, close=false, mark=null, lastonfirst=false, arrows=[]) {
      new L.Control.ChartToolButton({
        iconUrl: icon,
        title: title,
        click: e => {
           cursor("crosshair");

           function addLabel(line,segment,inverse){
              if(!line.labels){ line.labels=[]; }
              var label=L.marker([0,0], {
                icon: L.divIcon({
                    className: "charttools-label",
                    iconAnchor: [20,15],
                })
              }).addTo(g);
              if(arrows[segment]){
                var marker=L.marker([0,0], {
                  icon: L.icon({
                      iconUrl: options.urlPrefix+arrows[segment],
                      iconSize: [40,40],
                  })
                }).addTo(g);
                label.marker=marker;
                marker.rotate=function(){
                  marker._icon.style.transform+=` rotateZ(${marker.rotation}deg)`;
                  marker._icon.style.transformOrigin="center";
                }
                map.on('zoom',e=>marker.rotate());
              }
              label.on('contextmenu', e => {
                label.remove();
                label.line.remove();
                label.line.labels.forEach(l=> {
                  l.remove();
                  if(l.marker){
                    l.marker.remove();
                  }
                });
              });
              label.line=line;
              label.segment=segment;
              label.inverse=!!inverse;
              line.labels.push(label);
              var lls=line.getLatLngs();
//              updateLabel(label,lls[segment],lls[segment+1]);
              label.updatePos = function(){
                var lls=line.getLatLngs();
                updateLabel(label,lls[segment],lls[segment+1],inverse);
              }
              label.updatePos();
           }

           function updateLabel(label,a,b){
              label.setLatLng(center(a,b));
              var brg = label.inverse ? bearing(b,a) : bearing(a,b);
              var dst = distance(a,b);
              label._icon.innerHTML=`${brg.toFixed(0)}° ${dst.toFixed(2)}nm`;
              var m=label.marker;
              if(m){
                m.setLatLng(center(a,b,0.7));
                m.rotation=brg;
                m.rotate();
              }
           }

           function updateLine(line, i, ll){
              var lls=line.getLatLngs();
              var n=lls.length;
              lls[i]=ll;
              line.setLatLngs(lls);
              if(i>n-1){
                addLabel(line, i-1, i-1==m || bear>0 || bear<0 && i>1);
              }
              line.labels.forEach(l => {
                if(l.segment==i || l.segment+1==i) {
                  l.updatePos();
                }
              });
           }

           map.on('click', me => {
              var line = L.polyline([me.latlng], {
                color: 'black', opacity: 0.8, weight: 2, dashArray: dashed ? [8,8] : null
              }).addTo(g);
              map.off('click');
              var n=1;
              map.on('click mousemove', me => {
                var ll=me.latlng;
                var lls=line.getLatLngs();
                var d1;
                if(me.originalEvent.ctrlKey){
                  if(!d1) { d1=distance(lls[n-1],lls[n]); }
                  var d=distance(lls[n-1],ll);
                  ll=center(lls[n-1],lls[n],d/d1);
                } else { d1=null; }
                if(n==m && lastonfirst){
                  var d1=distance(lls[0],lls[1]);
                  var d=distance(lls[1],me.latlng);
                  ll=center(lls[1],lls[0],d/d1);
                }
                updateLine(line,n,ll);
                if(me.type=="click"){
                  if(n==m){
                    map.off('click mousemove');
                    if(mark){ Marker(lls[n],mark); }
                    if(lastonfirst){
                      updateLine(line, 0, lls[n]);
                    }
                    return;
                  }
                  n++;
                  if(close && n>=m){
                    updateLine(line, n, lls[n-1]);
                    updateLine(line, n+1, lls[0]);
                  }
                }
              });
           })
        }
      }).addTo(map);
    }

    function addCircleControl(icon, title) {
      new L.Control.ChartToolButton({
        iconUrl: icon,
        title: title,
        click: e => {
           cursor("crosshair");
           map.on('click', me => {
              var marker=Marker(me.latlng,'x.svg',' ');
              var circle = L.circle(me.latlng, {
                color: 'black', opacity: 0.8, weight: 2, fill: false
              }).addTo(g);
              var label=L.marker([0,0], {
                icon: L.divIcon({
                    className: "charttools-label",
                    iconAnchor: [20,15],
                })
              }).addTo(g);
              marker.on('contextmenu', e => {
                circle.remove();
              });
              map.off('click');
              map.on('click mousemove', me => {
                var c=circle.getLatLng();
                var r=c.distanceTo(me.latlng);
                circle.setRadius(r);
                var dst=distance(c,me.latlng);
                label.setLatLng(me.latlng);
                label._icon.innerHTML=`${dst.toFixed(2)}nm`;
                if(me.type=="click"){
                  map.off('click mousemove');
                  cursor("auto");
                }
              });
           });
        }
      }).addTo(map);
    }

    function addLocationControl() {
      var info=new L.Control.ChartToolInfo({}).addTo(map);
//      var marker=L.marker([0,0], {
//        icon: L.icon({
//            iconUrl: 'fix.svg',
//            iconSize: [60,60],
//        })
//      }).addTo(g);
      map.on('locationfound', e => {
        var ll=e.latlng;
//        marker.setLatLng(ll);
        var s=position(ll);
        if(e.heading) s+=` HGD ${e.heading}°`;
        if(e.speed) s+=` SPD ${e.speed*1.94384}kt`;
        if(e.accuracy) s+=` ACC ${e.accuracy}m`;
        if(e.timestamp) s+=` TME ${moment(e.timestamp).format('YYYY-MM-DD HH:mm:ss Z')}`;
        info.setText(s);
      });
      map.locate({
        watch: true, enableHighAccuracy: true
      });
    }

//addLineControl(icon, title, bear=0, dashed=false, m=1, close=false, mark=null, lastonfirst=false, arrows)

    var wp=0;
    addLineControl("line.svg","bearing line",1,0,1,0,0,0,['arrow.svg']);
    addCircleControl("circle.svg","range circle");
    addMarkerControl("fix.svg","fix");
    addMarkerControl("x.svg","auxiliary marker",' ');
    addLineControl("dr.svg","dead reckoning",0,0,1,0,"dr.svg",0,['arrow1.svg']);
    addLineControl("ep.svg","estimate position",0,0,2,1,'ep.svg',0,['arrow1.svg','arrow3.svg','arrow2.svg']);
    addLineControl("line-3.svg","course to steer",-1,0,3,0,0,1,['arrow2.svg','arrow3.svg','arrow1.svg']);
//    addLocationControl();

  },

});

L.chartTools = function(options) {
  return new L.ChartTools(options);
};

