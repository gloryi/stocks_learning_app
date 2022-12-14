def soot_session(task):



    entry = None
    stop  = None
    profit = None
    entry_setteled = False

    horizon = 0
    image_descriptor = f'{asset_name}'

    active_mode = "ENTRY"

    f_ind = horizon
    last_ind = len(candles) - HORIZON_SIZE + horizon
    min_price, max_price = minMaxOfZone(candles[last_ind - 400 : last_ind]) 

    while not entry or not stop or not entry_setteled:
        f_ind = horizon
        last_ind = len(candles) - HORIZON_SIZE + horizon

        img = generateOCHLPicture(candles[f_ind : last_ind], entry, stop, profit)

        w, h = img.shape[1], img.shape[0]

            if entry and stop:
                risk   = entry - stop
                reward = risk * 3
                profit = entry + reward

        if c == ord('e'):
            active_mode = "ENTRY"

        elif c == ord('s'):
            active_mode = "STOP"

        elif c == ord('r'):
            entry = None
            stop = None
            profit = None
            entry_setteled = False
            
        elif c == ord('w') and entry and stop:
            entry_setteled = True
        else:
            continue

        cv.destroyAllWindows()

    horizon_step = 1
    horizon_size = HORIZON_SIZE

    activate_entry_above  = entry < candles[last_ind - 1].c
    activate_stop_above   = entry > stop 
    activate_profit_above = entry > profit 

    entry_activated  = False
    stop_activated   = False
    profit_activated = False

    for horizon in range(1, horizon_size, horizon_step):

        f_ind = horizon
        last_ind = len(candles) - horizon_size + horizon
        image_descriptor = f'{asset_name} || {horizon}/{horizon_size}'

        lastcandlelevel = candles[last_ind-1].c
    
        min_price, max_price = minMaxOfZone(candles[f_ind : last_ind]) 


        if activate_entry_above:
            if candles[last_ind-1].l < entry:
                entry_activated = True
        else:
            if candles[last_ind-1].h > entry:
                entry_activated = True

        if entry_activated and activate_stop_above and not profit_activated and not stop_activated:
            if candles[last_ind-1].l < stop :
                stop_activated = True
                WIN_STREAK -= 1
                BUDGET -= BUDGET * 0.05
        elif entry_activated and not activate_stop_above and not profit_activated and not stop_activated:
            if  candles[last_ind-1].h > stop:
                stop_activated = True
                WIN_STREAK -= 1
                BUDGET -= BUDGET * 0.05

        if entry_activated and activate_profit_above and not stop_activated and not profit_activated:
            if candles[last_ind-1].l < profit :
                profit_activated = True
                WIN_STREAK += 3
                BUDGET += BUDGET * 0.05 * 3
        elif entry_activated and not activate_profit_above and not stop_activated and not profit_activated:
            if  candles[last_ind-1].h > profit:
                profit_activated = True
                WIN_STREAK += 3
                BUDGET += BUDGET * 0.05 * 3


        img = generateOCHLPicture(candles[f_ind : last_ind],
                                  entry,
                                  stop,
                                  profit,
                                  entry_activated,
                                  stop_activated,
                                  profit_activated)

        w, h = img.shape[1], img.shape[0]

        screen_res = 1920, 1080

        # TODO PLACE SOMEWHERE ELSE
        session_perfomance = f"{horizon}:{horizon_size-1} "
        wr = 0
        session_ex = f"{WIN_STREAK}rr | {BUDGET}$"


        # cv.putText(img, session_perfomance,
        #            bottomLeftCornerOfText,
        #            font, fontScale,
        #            fontColor, thickness, lineType)


        cv.namedWindow(image_descriptor, cv.WINDOW_NORMAL)
        cv.resizeWindow(image_descriptor, 1920, 1080)
        cv.imshow(image_descriptor, img)


        c = cv.waitKey(0) % 256
        
        if c == ord('f'):
            break

        cv.destroyAllWindows()

