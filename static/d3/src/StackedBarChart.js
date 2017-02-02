/**
 * @param {string} sSvgId the id of the svg
 * @param {array} aData array containing objects of type 
                  {
                    "key" : sName,
                    "data" : { //map containing the data
                      key1 : value1, // arbitrary key and value
                      ...
                    }
                  }
*/
function StackedBarChart(oParentId, aData) {
  var VIEWBOX = [0, 0, 1000, 500];

  var oSvg = d3.select("#" + oParentId).append("svg").attr("viewBox", VIEWBOX.join(" "));

  var MARGIN = {top: 120, right: 80, bottom: 20, left: 80},
      WIDTH = VIEWBOX[2] - MARGIN.left - MARGIN.right,
      HEIGHT = VIEWBOX[3] - MARGIN.top - MARGIN.bottom;

  oSvg.attr("class", "stackedBarChartContainer");

  var g = oSvg.append("g")
    .attr("transform", "translate(" + MARGIN.left + "," + MARGIN.top + ")")
    .attr("class", "stackedBarChart");

  var aKeys = aData.map(oData => oData.key);
  

  var oStack = d3.stack().keys(Object.keys(aData[0].data));
  var aSeriesData = d3.transpose(oStack(aData.map(oData => oData.data)));
  // add keys to data array
  aSeriesData.forEach(function(aData, iIndex) {
    aData.key = aKeys[iIndex];
  });
  // find max y
  var fY1Max = 1.1 * d3.max(aSeriesData, function(y) { return d3.max(y, function(d) { return d[1]; }); });

  // set tooltip layout
  tip.html(function(d) { 
    var oData = d[0].data;
    var sHtml = "<div class = 'title' >" + d.key + '</div>' + "<hr>" ;
    Object.keys(oData).forEach(function(sKey) {
      sHtml = sHtml + "<span class = 'key'>" + sKey + ": </span>" + oData[sKey] + "<br>";
    });
    return sHtml })

  g.call(tip);

  var x = d3.scaleBand()
      .domain(aKeys)
      .rangeRound([0, WIDTH])
      .padding(0.08);

  var y = d3.scaleLinear()
      .domain([0, fY1Max])
      .range([HEIGHT, 0]);

  var color = d3.scaleOrdinal()
      .domain(d3.range(aData.length))
      .range(d3.schemeCategory20c);

  // add axes
  g.append("g")
    .attr("class", "x axis ")
    .attr("transform", "translate(0," + HEIGHT + ")")
    .call(d3.axisBottom(x)
        .tickSize(0)
        .tickPadding(6));

  g.append("g")
    .attr("class", "y axis")
    .call(d3.axisLeft(y));

  // add groups for each stacked bar
  var series = g.selectAll(".series")
    .data(aSeriesData)
    .enter().append("g")
    .attr("class", "stackedBar")      
    .attr("transform", function(d, i) {
      var fOffset = (x.paddingOuter() + i) * x.step();
      return "translate(" + fOffset + ",0)";
    }) 
    .on('mouseover', function(d) {
      var that = this;
      series.classed("notHovered", function() {
        return that !== this;
      });
      tip.show(d, this);
    })
    .on('mouseout', function() {
      series.classed("notHovered", false);
      tip.hide();
    });

  // draw rects for each stacked bar
  var rect = series.selectAll("rect")
    .data(function(d, i) {
      return d;
    })
    .enter().append("rect")    
    .attr("data-legend",function(d) { return d.name})
    .attr("fill", function(d, i) { 
      return color(i + 8); }) 
    .attr("y", function(d) { 
      return y(d[1]); })
    .attr("width", x.bandwidth())
    .attr("height", function(d) { return y(d[0]) - y(d[1]); })  ;

}