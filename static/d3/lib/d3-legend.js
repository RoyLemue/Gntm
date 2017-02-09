// d3.legend.js 
// (C) 2012 ziggy.jonsson.nyc@gmail.com
// MIT licence

(function() {
    d3.legend = function(g) {
      g.each(function() {
        var g= d3.select(this),
            items = {},
            svg = d3.select(g.property("nearestViewportElement")),
            legendPadding = g.attr("data-style-padding") || 5,
            lb = g.selectAll(".legend-box").data([true]),
            li = g.selectAll(".legend-items").data([true])

        var legendBox = lb.enter().append("rect").classed("legend-box",true)
        var listItems = li.enter().append("g").classed("legend-items",true)

        svg.selectAll("[data-legend]").each(function() {
            var self = d3.select(this)
            items[self.attr("data-legend")] = {
              pos : self.attr("data-legend-pos") || this.getBBox().y,
              color : self.attr("data-legend-color") != undefined ? self.attr("data-legend-color") : self.style("fill") != 'none' ? self.style("fill") : self.style("stroke") 
            }
          })

        items = d3.entries(items).sort(function(a,b) { return a.value.pos-b.value.pos})

        
        listItems.selectAll("text")
            .data(items,function(d) { return d.key})
            .enter()
            .append("text")
            .attr("y",function(d,i) { return 1.1 * i+"em"})
            .attr("x","1em")
            .text(function(d) { return d.key})
        
        listItems.selectAll("circle")
            .data(items,function(d) { return d.key})
            .enter()
            .append("circle")
            .attr("cy",function(d,i) { return 1.1 * i-0.25+"em"})
            .attr("cx",0)
            .attr("r","0.4em")
            .style("fill",function(d) { return d.value.color})  
        
        // Reposition and resize the box
        var lbbox = listItems._groups[0][0].getBBox()  
        legendBox.attr("x",(lbbox.x-legendPadding))
            .attr("y",(lbbox.y-legendPadding))
            .attr("height",(lbbox.height+2*legendPadding))
            .attr("width",(lbbox.width+2*legendPadding))
      })
      return g
    }
})()