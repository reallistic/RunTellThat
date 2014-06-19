% include('base.tpl')
<body>
<div id="plex" class="application">
    <div class="nav-bar">
        <ul class="nav nav-bar-nav">
          <li><a class="back-btn" href="#" data-original-title="" title=""><i class="glyphicon left-arrow"></i></a></li>
          <li><a class="home-btn" href="#" data-original-title="" title=""><i class="glyphicon home"></i></a></li>
        </ul>
    </div>
    <div id="content" class="scroll-container minimal-scroll">
        <div class="container">
            <h3>RTTServer - Settings</h3>
            <div class="settings-container">
                <div class="server-settings-container">
                    <div class="filter-bar">                      
                        <span id="primary-server-dropdown" class="dropdown">
                        % server_name = config["RTTServer"]["FriendlyName"]
                          <span class="dropdown-placeholder">{{server_name}}</span>
                        </span>
                    </div>
                    <div class="settings-row row">
                        <div class="col-sm-4 col-md-3">
                            <ul class="settings-nav nav nav-stacked nav-sidebar">
                                % first = " selected"
                                % for section in config.keys():
                                    <li class="">
                                        <a class="btn-gray{{first}}" href="#{{section}}">{{section}}</a>
                                    </li>
                                    % first = ""
                                % end
                            </ul>
                        </div>
                        <div class="col-sm-8 col-md-9">
                            <form id="server-settings-form" method="POST">
                                % first = " active"
                                % for section in config.keys():
                                    <div id="{{section}}-group" class="settings-group{{first}}">
                                    % first = ""
                                    % firstkey = True
                                    % type = config[section]["Type"]
                                    % for key in config[section].keys():
                                        % if key != "Type":                                        
                                        % val = config[section][key]
                                        % if not type: #Regular stuff
                                            <div class="form-group">
                                            % if val in ["True", "False"]:
                                                % checked = ""
                                                % if val == "True":
                                                    % checked = "checked"
                                                % end
                                                <label class="control-label" for="{{section}}_{{key}}">
                                                <input type="checkbox" id="{{section}}_{{key}}" name="{{section}}_{{key}}" value="True" {{checked}}> {{key}}
                                                </label>
                                            % end
                                            % if val not in ["True", "False"]:
                                                <label class="control-label" for="{{section}}_{{key}}">{{key}}</label>
                                                <input type="text" id="{{section}}_{{key}}" class="form-control" name="{{section}}_{{key}}" value="{{val}}">
                                            % end
                                            % if section in desc and key in desc[section]:
                                                % cdesc = desc[section][key]
                                                <p class="help-block">{{cdesc}}</p>
                                            % end
                                            </div> <!-- end form-group -->
                                        % end # end regular stuff

                                        % if type == "list": #Lists
                                            <div class="form-group">
                                            % if firstkey:

                                                <label class="control-label" for="{{section}}[]">{{section}}</label>
                                            % end
                                            <input type="text" id="{{section}}[]" class="form-control" name="{{section}}[]" value="{{val}}">
                                            </div><!-- end form group -->
                                        % end # End lists

                                        % if type == "dict": #Key value pairs
                                            % if firstkey:
                                                <div class="form-group">
                                                <table class="table">
                                                    <tr>
                                                        <td>
                                                            <label class="control-label" for="{{section}}_key[]">{{section}} key</label>
                                                        </td>
                                                        <td>
                                                            <label class="control-label" for="{{section}}_value[]">{{section}} value</label>
                                                        </td>
                                                    </tr>
                                            % end
                                                <tr>
                                                    <td>
                                                        <input type="text" id="{{section}}_key[]" class="form-control" name="{{section}}_key[]" value="{{key}}">
                                                    </td>
                                                    <td>
                                                        <input type="text" id="{{section}}_value[]" class="form-control" name="{{section}}_value[]" value="{{val}}">
                                                    </td>
                                                </tr>
                                        % end #end dict
                                        % firstkey = False
                                        % end
                                    % end # end key in section loop
                                    % if type == "dict":
                                        </table>
                                    % end
                                    % if type in ["list","dict"]:
                                        % if section == "UserMachineIdentifiers":
                                            <a href="#" data-toggle="modal" data-target="#UserMachineIdentifiers"><span class="glyphicon plus"></span> Add</a>
                                        % else:
                                            <a href="#" class="add-form-group" data-type="{{type}}" data-section="{{section}}"><span class="glyphicon plus"></span> Add</a>
                                        % end
                                        % if section in desc:
                                            % cdesc = desc[section]
                                            <p class="help-block">{{cdesc}}</p>
                                        % end
                                    % end
                                    % if type == "dict":
                                        </div> <!-- end form-group -->
                                    % end
                                    % first = ""
                                    </div> <!-- end settings-group -->
                                % end # end section in config loop
                                <div class="form-footer">
                                  <button type="submit" class="submit-btn btn btn-lg btn-primary btn-loading">
                                    <div class="loading loading-sm"></div>
                                    <span class="btn-label">Save Changes</span>
                                  </button>
                                  <span class="form-message"></span>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
            % end
        </div>
    </div>
</div>
<!-- Modal -->
<div class="channel-settings-modal modal fade in" id="UserMachineIdentifiers" role="dialog" aria-labelledby="UserMachineIdentifiersLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title" id="UserMachineIdentifiersLabel">Add Ghosted User</h4>
            </div>
            <div class="modal-body">
                <form id="UserMachineIdentifiersForm">
                <div class="row">
                    <div class="col-xs-6 col-md-6 form-group">
                        <input type="text" class="form-control" placeholder="username" name="username" id="username" value="" required="true">
                    </div>
                    <div class="col-xs-6 col-md-6 form-group">
                        <input type="password" class="form-control" placeholder="password" name="password" id="password" value="" required="true">
                    </div>
                </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                <button type="submit" class="submit-btn btn btn-lg btn-primary btn-loading">
                    <div class="loading loading-sm"></div>
                    <span class="btn-label">Submit</span>
                </button>
                <span class="form-message"></span>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript" src="https://code.jquery.com/jquery-1.11.1.min.js"></script>
<script src="https://netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>
<script type="text/javascript">
    $(document).ready(function(){
        $("ul.settings-nav a.btn-gray").each(function(){
            $(this).click(function(e){
                $("ul.settings-nav a.btn-gray.selected").removeClass("selected");
                $(".settings-group.active").removeClass("active");
                $(this).addClass("selected");
                curGroup = $(this).attr("href")+"-group";
                $(curGroup).addClass("active");
                e.preventDefault();
            });
        });
        $("form#server-settings-form a.add-form-group").each(function(){
            $(this).click(function(e){
                if($(e.target).data("type") == "dict"){
                    $('<tr><td>'+
                        '<input type="text" id="'+$(e.target).data("section")+'_key[]" class="form-control" name="'+$(e.target).data("section")+'_key[]" value="">' +
                        '</td><td>'+
                        '<input type="text" id="'+$(e.target).data("section")+'_value[]" class="form-control" name="'+$(e.target).data("section")+'_value[]" value="">' +
                        '</td></tr>').appendTo("#"+$(e.target).data("section")+"-group table.table tbody");
                }
                else if($(e.target).data("type") == "list"){
                    $("#"+$(e.target).data("section")+"-group div.form-group:last").after('<div class="form-group">'+
                        '<input type="text" id="'+$(e.target).data("section")+'[]" class="form-control" name="'+$(e.target).data("section")+'[]" value="">' +
                        '</div>');
                }
                e.preventDefault();
            });
        });
        $("#UserMachineIdentifiers button.submit-btn").click(ghostUser);

        function ghostUser(e){
            $(this).addClass("active");
            $(this).off("click");
            $.post( "/ghost/", $( "#UserMachineIdentifiersForm" ).serialize(), function( data ) {
                if(data.error != ""){
                    $("#UserMachineIdentifiers span.form-message").text(data.error);
                }
                else{
                    $('<tr><td>'+
                    '<input type="text" id="UserMachineIdentifiers_key[]" class="form-control" name="UserMachineIdentifiers_key[]" value="'+data.myPlexUsername+'">' +
                    '</td><td>'+
                    '<input type="text" id="UserMachineIdentifiers_value[]" class="form-control" name="UserMachineIdentifiers_value[]" value="'+data.machineIdentifier+'">' +
                    '</td></tr>').appendTo("#UserMachineIdentifiers-group table.table tbody");
                    $("#UserMachineIdentifiers span.form-message").text("Ghosting successful");
                }
                $("#UserMachineIdentifiers button.submit-btn").click(ghostUser);
                $("#UserMachineIdentifiers button.submit-btn").removeClass("active");
            }, "json");
        }
    }); //End document ready
</script>
</body>
</html>
