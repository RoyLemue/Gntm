$( document ).ready(function(){
	console.log($("input[name='aktien']"));
	$("input[name='aktien']").change(function() {
		
		var model = $(this.form.model).val();
		var aktien = $(this).val();
		var textField =  $( this).next();
		$.getJSON(
			"/gntm/?ajax&model="+model+"&aktien="+aktien,
			function(data) {
				console.log(data.price);
				console.log($(this).next());
			  textField.text(data.price.summe.toFixed(2));
		});
	});
	console.log("attached");
});