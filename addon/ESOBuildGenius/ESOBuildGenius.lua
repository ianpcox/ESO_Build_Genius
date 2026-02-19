--[[
  ESO Build Genius – Addon mockup/skeleton.
  Provides a single window (Build Genius panel) with title bar and close button.
  Full implementation would:
  - Populate class/race/role/mundus/food/potion dropdowns from game API or sync with external backend.
  - Show 14 equipment slots and set recommendations (Advisor) using GetItemLinkSetInfo, etc.
  - Show 12-skill bar with scribing (Focus/Signature/Affix) when that API is available.
  See project docs (DATA_SOURCES.md, UI_DESIGN.md) and the HTML mockup in addon/mockup/ for the intended UI.
]]

ESOBuildGenius = ESOBuildGenius or {}
local ADDON_NAME = "ESOBuildGenius"

local function OnAddOnLoaded(_, addonName)
  if addonName ~= ADDON_NAME then return end

  -- SavedVariables (optional; for window position, last build choices, etc.)
  ESOBuildGenius.saved = ZO_SavedVars:NewAccountWide("ESOBuildGeniusSaved", 1, nil, {})

  -- Create main window from our XML template
  local window = WINDOW_MANAGER:CreateControlFromVirtual("ESOBuildGeniusWindowRoot", GuiRoot, "ESOBuildGeniusWindow")
  ESOBuildGenius.window = window

  -- Close button
  window:GetNamedChild("Close"):SetHandler("OnClicked", function()
    window:SetHidden(true)
  end)

  -- Optional: add content controls here (dropdowns, labels, scroll) using WINDOW_MANAGER:CreateControlFromVirtual
  -- or create child controls in Lua. For mockup we leave the content area empty; the HTML mockup shows the layout.

  -- Slash command to toggle window
  SLASH_COMMANDS["/buildgenius"] = function()
    window:SetHidden(not window:IsHidden())
  end

  -- Default: hidden on load so user can /buildgenius to show
  window:SetHidden(true)
end

EVENT_MANAGER:RegisterForEvent(ADDON_NAME, EVENT_ADD_ON_LOADED, OnAddOnLoaded)
