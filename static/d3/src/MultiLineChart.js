/**
 * @param {string} sSvgId the id of the svg
 * @param {array} aData array containing objects of type 
 *                 {
 *                   "key" : sName,
 *                   "data" : [{
 *                     "date" : date,
 *                     "val": value},
 *                     ...
 *                     ]
 *                 }
 * @param {Float} [fYMin=10] minimal y-axis value
*/
function MultiLineChart(sParentId, aData, fYMin) {
  var VIEWBOX = [0, 0, 1000, 500];

  var oSvg = d3.select("#" + sParentId).append("svg").attr("viewBox", VIEWBOX.join(" "));

  var MARGIN = {top: 40, right: 150, bottom: 20, left: 80},
      WIDTH = VIEWBOX[2] - MARGIN.left - MARGIN.right,
      HEIGHT = VIEWBOX[3] - MARGIN.top - MARGIN.bottom;

  var dMinDate = d3.min(aData, function(d) { 
    return d3.min(d.data, function(d) {
      return d.date;
    });

  });
  var dMaxDate = new Date();
  var fMaxValue = calcYMax(aData);


  oSvg.attr("class", "multiLineChartContainer");

  var g = oSvg.append("g")
    .attr("transform", "translate(" + MARGIN.left + "," + MARGIN.top + ")")
    .attr("class", "multiLineChart");

  var x = d3.scaleTime()
    .domain([dMinDate, dMaxDate])
    .range([0, WIDTH]);

  if (!fYMin) {
    fYMin = 10;
  }
  var y = d3.scaleLinear()
    .domain([fYMin, fMaxValue])
    .range([HEIGHT, 0]);

  var color = d3.scaleOrdinal()
      .domain(aData.map(oData => oData.key))
      .range(d3.schemeCategory20);

  var xAxis = d3.axisBottom(x);
  var yAxis = d3.axisLeft(y);

  var line = d3.line()
    .x(function(d) { return x(d.date); })
    .y(function(d) { return y(d.val); });

  g.call(tip);

  // add axes
  g.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + HEIGHT + ")")
      .call(xAxis);

  g.append("g")
      .attr("class", "y axis")
      .call(yAxis);

  g.append("clipPath")       // define a clip path
    .attr("id", "canvas-clip") // give the clipPath an ID
    .append("rect")          // shape it as an ellipse
    .attr("x", 0)         // position the x-centre
    .attr("y", 0)         // position the y-centre
    .attr("height", HEIGHT)         // set the x radius
    .attr("width", WIDTH);         // set the y radius

  // add
  var aLines = g.selectAll(".lineContainer")
      .data(aData)
      .enter().append("g")
      .attr("class", "lineContainer")      
      .on('mouseover', function(d) {
        var that = this;
        aLines.classed("notHovered", function() {
          return that !== this;
        });

        // set tooltip layout
        tip.html(function(d) { 
          var sHtml = "<span class = 'title' >" + d.key + '</span>' + "<hr>" ;
          sHtml = sHtml + "<span class = 'key'>Wert: </span>" + d.data[d.data.length - 1].val;
          return sHtml 
        });

        tip.show(d, this);
      })     
      .on('mouseout', function() {
        var that = this;
        aLines.classed("notHovered", false);
        tip.hide();
      });

  aLines.append("path")
      .attr("class", "line")
      .attr("clip-path", "url(#canvas-clip)") // clip the path
      .attr("d", function(d) { return line(d.data); })
      .attr("data-legend",function(d) { return d.key})
      .style("stroke", function(d) { 
        return color(d.key); });

  // add legend
  var legend = oSvg.append("g")
    .attr("class","legend")
    .attr("transform","translate(" + (MARGIN.left + WIDTH + 30) + ",0)")
    .call(d3.legend);

  // add time axis buttons
  var aButtonData = [{label: "15M", x: WIDTH / 2 - 200, y: MARGIN.top / 4, timeOffset : 15 * 60 * 1000 },
            {label: "1H", x: WIDTH / 2 - 100, y: MARGIN.top / 4, timeOffset : 60 * 60 * 1000 },
            {label: "24H", x: WIDTH / 2, y: MARGIN.top / 4, timeOffset : 24 * 60 * 60 * 1000 },
            {label: "1W", x: WIDTH / 2 + 100, y: MARGIN.top / 4, timeOffset : 7 * 24 * 60 * 60 * 1000  },
            {label: "ALL", x: WIDTH / 2 + 200, y: MARGIN.top / 4, timeOffset : -1 }];

  var button = d3.button()
    .on('press', function(d, i) { 
      clearAll();      
      var dXMin = d.timeOffset > 0 ? dMaxDate - d.timeOffset : dMinDate;
      updateXMin(dXMin);
    });

  // Add buttons
  var buttons = g.selectAll('.button')
      .data(aButtonData)
      .enter()
      .append('g')
      .attr('class', 'button')
      .call(button);

  function clearAll() {
    buttons.selectAll('rect')
        .each(function(d, i) { button.clear.call(this, d, i) });
  }


  function updateXMin(dXMin) {
     // create a deep copy of data and filter for the new key value pairs
    var aFilteredData = aData.map(function(oData) {
      var aFilteredDatePairs = oData.data.filter(function(oPair) {
        return oPair.date >= dXMin;
      });
      return {
        key : oData.key,
        data : aFilteredDatePairs
      };
    });

    // Scale the range of the data again 
    x.domain([dXMin, dMaxDate]);
    y.domain([fYMin, calcYMax(aFilteredData)]);

    // // Make the changes
    aLines.selectAll(".line")   // change the line
       .attr("d", function(d) {
        return line(d.data);
       });
    g.select(".x.axis") // change the x axis
       .call(xAxis);
    g.select(".y.axis") // change the y axis
       .call(yAxis);
  };

  function calcYMax(aData) {
    return 1.1 * d3.max(aData, function(d) { 
      return d3.max(d.data, function(d) {
        return d.val;
      });
    });
  }

}