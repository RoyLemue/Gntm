/**
 * @param {string} sSvgId the id of the svg
 * @param {array} aData array containing objects of type 
                  {
                    "key" : sName,
                    "data" : [{
                      "date" : date,
                      "val": value},
                      ...
                      ]
                  }
*/
function MultiLineChart(sParentId, aData) {
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
  var fMaxValue = 1.1 * d3.max(aData, function(d) { 
    return d3.max(d.data, function(d) {
      return d.val;
    });
  });


  oSvg.attr("class", "multiLineChartContainer");

  var g = oSvg.append("g")
    .attr("transform", "translate(" + MARGIN.left + "," + MARGIN.top + ")")
    .attr("class", "multiLineChart");

  var x = d3.scaleTime()
    .domain([dMinDate, dMaxDate])
    .range([0, WIDTH]);

  var y = d3.scaleLinear()
    .domain([0, fMaxValue])
    .range([HEIGHT, 0]);

  var color = d3.scaleOrdinal()
      .domain(aData.map(oData => oData.key))
      .range(d3.schemeCategory20);

  var xAxis = d3.axisBottom(x);
  var yAxis = d3.axisLeft(y);

  var line = d3.line()
    .x(function(d) { return x(d.date); })
    .y(function(d) { return y(d.val); });

  // add axes
  g.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + HEIGHT + ")")
      .call(xAxis);

  g.append("g")
      .attr("class", "y axis")
      .call(yAxis);

  // add
  var aLines = g.selectAll(".lineContainer")
      .data(aData)
      .enter().append("g")
      .attr("class", "lineContainer")      
      .on('mouseover', function() {
        var that = this;
        aLines.classed("notHovered", function() {
          return that !== this;
        });
      })     
      .on('mouseout', function() {
        var that = this;
        aLines.classed("notHovered", false);
      });

  aLines.append("path")
      .attr("class", "line")
      .attr("d", function(d) { return line(d.data); })
      .attr("data-legend",function(d) { return d.key})
      .style("stroke", function(d) { 
        return color(d.key); });

  // add legend
  var legend = g.append("g")
    .attr("class","legend")
    .attr("transform","translate(" + WIDTH + ",0)")
    .call(d3.legend)

}