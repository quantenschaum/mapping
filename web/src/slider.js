// from https://github.com/svitkin/leaflet-timeline-slider

// TODO: parameterize timeline colors, overall length, and length between points (css styles)
L.Control.TimeLineSlider = L.Control.extend({
  options: {
    position: "bottomright",
    timelineItems: ["Today", "Tomorrow", "The Next Day"],

    changeMap: function ({ label, value, map }) {
      console.log(
        "You are not using the value or label from the timeline to change the map.",
      );
    },
    extraChangeMapParams: {},
    initializeChange: true,

    knobSize: 4,
    labelWidth: 40,
    betweenLabelAndRangeSpace: 15,

    labelFontSize: "1.2em",
    activeColor: "#1862b8",
    inactiveColor: "#555555",

    backgroundOpacity: 1,
    backgroundColor: "#ffffff",

    topBgPadding: "1em",
    bottomBgPadding: "2em",
    rightBgPadding: "2em",
    leftBgPadding: "2em",

    button: "Timeline",
    heading: "Timeline",
    collapsed: true,
  },

  initialize: function (options) {
    if (typeof options.changeMap != "function") {
      options.changeMap = function ({ label, value, map }) {
        console.log(
          "You are not using the value or label from the timeline to change the map.",
        );
      };
    }

    if (parseFloat(options.knobSize) <= 2) {
      console.log(
        "The nodes on the timeline will not appear properly if its radius is less than 2px.",
      );
    }

    L.setOptions(this, options);
  },

  onAdd: function (map) {
    this.map = map;
    this.sheet = document.createElement("style");
    document.body.appendChild(this.sheet);

    this.container = L.DomUtil.create(
      "div",
      "slider_container leaflet-bar leaflet-control",
    );

    /* Prevent click events propagation to map */
    L.DomEvent.disableClickPropagation(this.container);

    /* Prevent right click event propagation to map */
    // L.DomEvent.on(this.container, "slider_container", function (ev) {
    //   L.DomEvent.stopPropagation(ev);
    // });

    /* Prevent scroll events propagation to map when cursor on the div */
    L.DomEvent.disableScrollPropagation(this.container);

    /* Create html elements for input and labels */
    this.slider = L.DomUtil.create("div", "slider", this.container);
    this.title = L.DomUtil.create("div", "title", this.slider);
    this.title.innerHTML = this.options.title;
    this.range = L.DomUtil.create("div", "range", this.slider);
    this.range.innerHTML = `<input id="rangeinputslide" type="range" min="1" max="${this.options.timelineItems.length}" steps="1" value="1"></input>`;

    this.rangeLabels = L.DomUtil.create("ul", "range-labels", this.slider);
    this.rangeLabels.innerHTML = this.options.timelineItems
      .map((item) => "<li><span>" + item + "</span></li>")
      .join("");

    this.rangeLabelArray = Array.from(
      this.rangeLabels.getElementsByTagName("li"),
    );
    this.sliderLength = this.rangeLabelArray.length;

    this.thumbSize = parseFloat(this.options.knobSize) * 2;
    // double the thumb size when its active
    this.activeThumbSize = this.thumbSize * 2;

    // make the width of the range div holding the input the number of intervals * the label width and add the thumb size on either end of the range
    this.rangeWidthCSS =
      parseFloat(this.options.labelWidth) *
        (this.options.timelineItems.length - 1) +
      this.thumbSize * 2;
    console.log("rangeWidthCSS", this.rangeWidthCSS);

    // move labels over to the left so they line up; move half the width of the label and adjust for thumb radius
    this.rlLabelMargin =
      parseFloat(this.options.labelWidth) / 2 -
      parseFloat(this.options.knobSize) / 2;
    console.log("rlLabelMargin", this.rlLabelMargin);

    // 2.5 because that is half the height of the range input
    this.topLabelMargin =
      parseFloat(this.options.betweenLabelAndRangeSpace) -
      parseFloat(this.options.knobSize) -
      2.5;
    console.log("topLabelMargin", this.topLabelMargin);

    this.backgroundRGBA = this.hexToRGBA(
      this.options.backgroundColor,
      this.options.backgroundOpacity,
    );
    this.coverBackgroundRGBA = this.hexToRGBA(this.options.backgroundColor, 0);

    let that = this;

    this.sheet.textContent = this.setupStartStyles();

    /* When input gets changed change styles on slider and trigger user's changeMap function */
    this.rangeInput = this.range.children[0];
    L.DomEvent.on(this.rangeInput, "input", function () {
      let curValue = this.value;

      that.sheet.textContent += that.getTrackStyle(this, that.sliderLength);
      let curLabel = that.rangeLabelArray[curValue - 1].textContent;

      // Change map according to either current label or value chosen
      let mapParams = { value: curValue, label: curLabel, map: map };
      let allChangeMapParameters = {
        ...mapParams,
        ...that.options.extraChangeMapParams,
      };
      that.options.changeMap(allChangeMapParameters);
    });

    // Add click event to each label so it triggers input change for corresponding value
    this.rangeLabelArray.forEach((li, index) => {
      L.DomEvent.on(li, "click", function (e) {
        that.rangeInput.value = index + 1;
        that.rangeInput.dispatchEvent(new Event("input"));
      });
    });

    // Initialize input change at start
    if (this.options.initializeChange) {
      var inputEvent = new Event("input");
      this.rangeInput.dispatchEvent(inputEvent);
    }

    this.menu = L.DomUtil.create("div", "menu hide", this.container);
    this.menu.innerHTML = this.options.button;
    this.container.addEventListener("mouseenter", () => {
      console.log("show");
      this.menu.classList.add("hide");
      this.slider.classList.remove("hide");
    });
    this.container.addEventListener("mouseleave", () => {
      console.log("hide");
      this.menu.classList.remove("hide");
      this.slider.classList.add("hide");
    });
    if (this.options.collapsed) {
      this.menu.classList.remove("hide");
      this.slider.classList.add("hide");
    }
    return this.container;
  },

  onRemove: function () {
    // remove control html element
    L.DomUtil.remove(this.container);
  },

  hexToRGBA: function (hex, opacity) {
    // from https://stackoverflow.com/questions/21646738/convert-hex-to-rgba
    var c;
    if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
      c = hex.substring(1).split("");
      if (c.length == 3) {
        c = [c[0], c[0], c[1], c[1], c[2], c[2]];
      }
      c = "0x" + c.join("");
      return (
        "rgba(" +
        [(c >> 16) & 255, (c >> 8) & 255, c & 255].join(",") +
        "," +
        opacity +
        ")"
      );
    }
    throw new Error("Bad Hex");
  },

  setupStartStyles: function () {
    const style = `
      @media (max-width: 660px) {
          .slider {
              transform: translateY(100%) rotate(90deg);
              transform-origin: 100% 0%;
          }
          .slider .range-labels li span {
              display: inline-block;
              transform: rotate(-90deg);
              transform-origin: 50% 50%;
          }
      }
      .slider_container .menu {
          padding: 1ex;
          background-color: ${this.backgroundRGBA};
      }
      .slider_container .hide {
          display: none;
      }
      .slider {
          background-color: ${this.backgroundRGBA};
          padding: ${this.options.topBgPadding} ${this.options.rightBgPadding} ${this.options.bottomBgPadding} ${this.options.leftBgPadding};
          font-size: ${this.options.labelFontSize};
      }
      .slider .title {
          text-align: center;
          margin: 0 ${this.rlLabelMargin}px 0.5em 0;
      }
      .slider .range {
          position: relative;
          left: -${this.thumbSize}px;
          height: 5px;
          width: ${this.rangeWidthCSS}px;
      }
      .slider .range input {
          width: 100%;
          position: absolute;
          height: 0px;
          -webkit-appearance: none;
      }
      /* -1 because the height is 2 (half the height) */
      .slider .range input::-webkit-slider-thumb {
          background: ${this.options.activeColor};
          margin: -${this.thumbSize - 1}px 0 0;
          width: ${this.activeThumbSize}px;
          height: ${this.activeThumbSize}px;
          -webkit-appearance: none;
          border-radius: 50%;
          cursor: pointer;
          border: 0 !important;
      }
      .slider .range input::-moz-range-thumb {
          background: ${this.options.activeColor};
          margin: -${this.thumbSize - 1}px 0 0;
          width: ${this.activeThumbSize}px;
          height: ${this.activeThumbSize}px;
          border-radius: 50%;
          cursor: pointer;
          border: 0 !important;
      }
      .slider .range input::-ms-thumb {
          background: ${this.options.activeColor};
          margin: -${this.thumbSize - 1}px 0 0;
          width: ${this.activeThumbSize}px;
          height: ${this.activeThumbSize}px;
          border-radius: 50%;
          cursor: pointer;
          border: 0 !important;
      }
      .slider .range input::-webkit-slider-runnable-track {
          background: ${this.options.inactiveColor};
          width: 100%;
          height: 2px;
          cursor: pointer;
      }
      .slider .range input::-moz-range-track {
          background: ${this.options.inactiveColor};
          width: 100%;
          height: 2px;
          cursor: pointer;
      }
      .slider .range input::-ms-track {
          background: ${this.options.inactiveColor};
          width: 100%;
          height: 2px;
          cursor: pointer;
          background: transparent;
          border-color: transparent;
          color: transparent;
      }
      .slider .range input:focus {
          background: none;
          outline: none;
      }
      .slider .range input[type=range]::-moz-focus-outer {
          border: none;
      }
      .slider .range-labels {
          margin: ${this.topLabelMargin}px -${this.rlLabelMargin}px 0;
          padding: 0;
          list-style: none;
      }
      .slider .range-labels li {
          color: ${this.options.inactiveColor};
          width: ${this.options.labelWidth}px;
          position: relative;
          float: left;
          text-align: center;
          cursor: pointer;
      }
      .slider .range-labels li::before {
          background: ${this.options.inactiveColor};
          width: ${this.thumbSize}px;
          height: ${this.thumbSize}px;
          position: absolute;
          top: -${this.options.betweenLabelAndRangeSpace}px;
          right: 0;
          left: 0;
          content: "";
          margin: 0 auto;
          border-radius: 50%;
      }
      .slider .range-labels .active {
          color: ${this.options.activeColor};
          font-weight: bold;
      }
      .slider .range-labels .active::before {
          display: none;
      }`;

    return style;
  },

  getTrackStyle: function (el, sliderLength) {
    let prefs = ["webkit-slider-runnable-track", "moz-range-track", "ms-track"];

    var curVal = el.value,
      labelIndex = curVal - 1,
      val = labelIndex * (100 / (sliderLength - 1)),
      coverVal = (parseFloat(this.thumbSize) / this.rangeWidthCSS) * 100;
    let style = "";

    for (let li of this.rangeLabelArray) {
      L.DomUtil.removeClass(li, "active");
    }

    // Find label that should be active and give it appropriate classes
    var curLabel = this.rangeLabelArray[labelIndex];
    L.DomUtil.addClass(curLabel, "active");

    console.log(style);

    return style;
  },
});

L.control.timelineSlider = function (options) {
  return new L.Control.TimeLineSlider(options);
};
