"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EventStatus = void 0;
// All event status
var EventStatus;
(function (EventStatus) {
    EventStatus[EventStatus["NOT_OPEN"] = 0] = "NOT_OPEN";
    EventStatus[EventStatus["REGISTERING"] = 1] = "REGISTERING";
    EventStatus[EventStatus["WAITLIST"] = 2] = "WAITLIST";
    EventStatus[EventStatus["CLOSED"] = 3] = "CLOSED";
    EventStatus[EventStatus["ENDED"] = 4] = "ENDED";
})(EventStatus || (exports.EventStatus = EventStatus = {}));
//# sourceMappingURL=event.interface.js.map