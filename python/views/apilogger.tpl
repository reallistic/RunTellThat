% include('base.tpl')
<body>
<div id="plex" class="application">
    <div id="content" class="scroll-container minimal-scroll">
        <div class="priorities-container">
            % id = 1
            % for uri in data:
                % request_uri = uri["uri"]
                % method = uri["method"]
                % querys = uri["querystrings"]
                % reqheaders = uri["headers"]
                % respheaders = uri["respheaders"]
            <div class="priority-{{id}}-container">
                <div class="dashboard-container">
                    <h3>{{request_uri}} {{method}}</h3>
                    <div class="dashboard-list-container" style="-webkit-transform: translate(0px, 0px);">
                        <ul class="tile-list media-tile-list horizontal-media-tile-list" style="width: 100%;">                            
                            <li class="poster-item media-tile-list-item movie show-subtitle">
                                <div>
                                    <div class="media-title media-heading">Query String params</div>
                                    <ul>
                                    % for query in uri["querystrings"]:
                                        % qs = query[0]
                                        <li>{{qs}}</li>
                                    % end
                                    </ul>
                                </div>
                            </li>
                            <li class="poster-item media-tile-list-item movie show-subtitle">
                                <div>
                                    <div class="media-title media-heading">Request Headers</div>
                                    <ul>
                                    % for header in reqheaders:
                                        % rh = header[0]
                                        <li>{{rh}}</li>
                                    % end
                                    </ul>
                                </div>
                            </li>
                            <li class="poster-item media-tile-list-item movie show-subtitle">
                                <div>
                                    <div class="media-title media-heading">Response Headers</div>
                                    <ul>
                                    % for header in respheaders:
                                        % rh = header[0]
                                        <li>{{rh}}</li>
                                    % end
                                    </ul>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
                % id +=1
            % end
        </div>
    </div>
  </div>
</body>
</html>
