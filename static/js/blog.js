// for blog 

var checkLogin = function(current_url){
	var user_name =$('.user-name-holder').text().trim();
	
	// if not logged in, redirect to login
	 if((! user_name) || user_name == null || user_name ==""){
		window.location.href = "/login?redirect="+current_url;
		return false;
	}

	var is_loggedin = $('.is-loggedin-holder').text().trim();
	if(is_loggedin == 0 || is_loggedin == '0' || is_loggedin == null ||
		is_loggedin ==""){
		window.location.href = "/login?redirect="+current_url;
		return false;
	}

	return true;
};


$("span.like-button").click(function(){
	console.log("like-button being cliked!");
	// alert( "Handler for .click() called." );
	// implement ajax
	var post_id = $(".post-id-holder").text();
	var post_like_url = '/blog/'+post_id+'/like';
	// alert("ajax: "+post_like_url);

	// check log in status
	if(!checkLogin('/blog/'+post_id)){
		console.log("log in first!");
		return;
	}

	$.post(post_like_url, function(data, status){
		// is Logged in 
		if(!data['isLogged']){
			// similar behavior as an HTTP redirect
			// window.location.replace("/login");
			// similar behavior as clicking on a link
			window.location.href = "/login?redirect="+'/blog/'+post_id;
		} else{
			if(data['canLike']){
				displayPostFooterError(false, "");
				// alert("response data: " +data['isAdd']);
				var isAdd = data['isAdd'];
				if(isAdd){
					appendLike();
				} else {
					deleteLike();
				}
			} else{
				displayPostFooterError(true, "You can not like your own post!");
			}
			
		}
	});
});

$("span.comment-button").click(function(){
	var post_id = $(".post-id-holder").text();
	// check log in status
	if(!checkLogin('/blog/'+post_id)){
		alert("log in first!");
		return;
	}

	$("#add-comment-textarea").focus();
});

$("#add-comment-textarea").click(function(){
	$(this).focus();
});

$("span.edit-button").click(function(){

	var post_id = $(".post-id-holder").text();
	// check log in status
	if(!checkLogin('/blog/'+post_id)){
		alert("log in first!");
		return;
	}

	
	var post_edit_url = '/blog/'+post_id+'/edit';

	var user_name =$('.user-name-holder').text().trim();
	var post_owner_name = $(".post-owner").text().trim();
	// alert(user_name+"?"+post_owner_name);
	if(user_name == post_owner_name){
		displayPostFooterError(false, "You can edit this post!");
		window.location.href = post_edit_url;
	} else{
		displayPostFooterError(true, "You can not edit other's post!");
	}

});

$(".delete-button").click(function(){

	var post_id = $(".post-id-holder").text();
	// check log in status
	if(!checkLogin('/blog/'+post_id)){
		alert("log in first!");
		return;
	}

	// alert( "Handler for .click() called." );
	var post_delete_url = '/blog/'+post_id+'/delete';

	var user_name =$('.user-name-holder').text().trim();
	var post_owner_name = $(".post-owner").text().trim();
	// alert(user_name+"?"+post_owner_name);
	if(user_name==""|user_name == null ||(!user_name)){
		window.location.href = "/login?redirect="+'/blog/'+post_id;


	}

	if(user_name == post_owner_name){
		displayPostFooterError(true, "You can delete this post!");
		// show pop up modal box
		$("#confirm-delete-modal").css("display", "block");

		// if($("#confirm-delete-modal")){alert("modal " );}
		

		$("span.yes").click(function(){
			$("#confirm-delete-modal").css("display", "none");
			// window.location.href = post_delete_url;
			$.post(post_delete_url, function(data, status){
				// is Logged in 
				if(!data['isLogged']){
					// similar behavior as an HTTP redirect
					// window.location.replace("/login");
					// similar behavior as clicking on a link
					window.location.href = "/login?redirect="+'/blog/'+post_id;
				} else{
					if(data['canDelete']){
						displayPostFooterError(false, "");
						// alert("response data: " +data['isAdd']);
						if(data['isDeleted']){
							displayPostFooterError(true, "Delete success");
							alert("delete success!");
							window.location.href="/flush";
							setTimeout(
							  function() 
							  {
							    window.location.href="/";
								// delete the post from the page in case of broser saving
								var post_container_id = '#post-id-'+post_id;
								var post_container = $(post_container_id);
								console.log(post_container);
								if(post_container.length){
									post_container.empty();
									post_container.remove();

								} else{

								}
							  }, 5000);



							
						}
					} else{
						displayPostFooterError(true, "You can not delete other's post!");
					}
					
				}
			});
		});
		$('span.no').click(function(){
			$("#confirm-delete-modal").css("display", "none");
		});
		

	} else{
		displayPostFooterError(true, "You can not delete other's post!");
	}

});

// when click x, close popup modal
$('span.close').click(function(){
	$("#confirm-delete-modal").css("display", "none");
});

// when click anywhere outside modal, close popup modal
window.onclick = function(event){
	var modal = $('#confirm-delete-modal');
	if (event.target == modal) {
        modal.css("display", "none");
    }
}


// action="/blog/{{post.key().id()}}/comment"
// method="post" onsubmit="return validateForm()"
$("#add-comment-submit").click(function(){

	var user_name =$('.user-name-holder').text().trim();
	
	// alert("user: "+user_name +"," + is_loggedin);
	 if((! user_name) || user_name == null || user_name ==""){
		window.location.href = "/login";
		return false;
	}

	var is_loggedin = $('.is-loggedin-holder').text().trim();
	if(is_loggedin == 0 || is_loggedin == '0' || is_loggedin == null ||
		is_loggedin ==""){
		window.location.href = "/login";
		return false;
	}

	var post_id = $(".post-id-holder").text();
	var post_comment_url = '/blog/'+post_id+'/comment';
	var content_text = $("#add-comment-textarea").val();
	content_text = content_text.trim();
	// alert("comment content: "+content_text);

	if(content_text == null || content_text == ""){
		$('.add-comment-error').show();
		return false;
	} else{
		$('.add-comment-error').hide();
		var user_name =$('.user-name-holder').text().trim();
		html_str = "<div class='comment-container'><section class='comment-created-info'>"+
					"<p><span class='comment-owner'>"+
					user_name +
					"</span> " +
					"<span class='comment-time text-right'> created on "+
					"just now"+
					"</span></p></section><section class='comment-content'><div >"+
					'"'+content_text+'"'+
					"</div></section><section class='comment-action'><div class=''>Edit</div>"+
					"<div class=''>Reply</div></section></div>";

		$("#comments-container").append(html_str);
		$("#add-comment-textarea").val("");

		$.post(post_comment_url, 
			{add_comment_content: content_text}, 
			function(data, status){
				if(data['isSuccess']){
					alert("comment add success!");
					
				}else{

				}
			});
	}
	
    
});


var appendLike = function(){
	// console.log("append like ...");
	var user_name =$('.user-name-holder').text();
	$("#likes-container").append("<span class='like-owner'>"+user_name+",</span>");
};

var deleteLike = function(){
	// console.log("delete like ...");
	var user_name =$('.user-name-holder').text();
	$("span.like-owner").each(function(index){
		var like_text = $(this).text().replace(",", "");
		like_text = like_text.trim();
		if ( like_text == user_name){
			$(this).remove();
		}
	});
};

var displayPostFooterError = function(isShown, message){
	if(isShown){
		$('.post-footer-error').text(message);
		$('.post-footer-error').fadeIn(400);
		$('.post-footer-error').delay(1000);
		$('.post-footer-error').fadeOut(400);
	} else{
		$('.post-footer-error').hide();
	}
	
};

