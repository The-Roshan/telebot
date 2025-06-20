const TelegramBot = require('node-telegram-bot-api');

// Replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token
const TOKEN = '';
// Replace 'OWNER_USER_ID_HERE' with the Telegram user ID of the owner
const OWNER_USER_ID = '';

// Global variables to control the message sending loop and channels list
let userRunningStatus = {};  // Object to store running status for each user
let userChannels = {};  // Object to store user-specific channel lists
let userStartingNumber = {};  // Object to store user-specific starting numbers
let userTargetChannel = {};  // Object to store user-specific target channels
let authorizedUsers = new Set();  // Set to store authorized user IDs
let userThreads = {};  // Object to store user-specific intervals

const bot = new TelegramBot(TOKEN, { polling: true });

function restricted(func) {
  return (msg, match) => {
    const userId = String(msg.from.id);
    if (userId !== OWNER_USER_ID && !authorizedUsers.has(userId)) {
      bot.sendMessage(msg.chat.id, "You are not authorized to use this bot.");
      return;
    }
    func(msg, match);
  };
}

function ownerOnly(func) {
  return (msg, match) => {
    const userId = String(msg.from.id);
    if (userId !== OWNER_USER_ID) {
      bot.sendMessage(msg.chat.id, "Only the bot owner can use this command.");
      return;
    }
    func(msg, match);
  };
}

function channelOwnerOnly(func) {
  return (msg, match) => {
    const userId = String(msg.from.id);
    if (!userChannels[userId]) {
      bot.sendMessage(msg.chat.id, "You don't have any channels added.");
      return;
    }
    func(msg, match);
  };
}

const start = channelOwnerOnly((msg) => {
  const userId = String(msg.from.id);
  if (!userRunningStatus[userId]) {
    userRunningStatus[userId] = true;
    bot.sendMessage(msg.chat.id, 'Bot started! Messages will be sent every minute.');
    
    userThreads[userId] = setInterval(() => sendMessages(userId), 60000);
  } else {
    bot.sendMessage(msg.chat.id, 'Bot is already running.');
  }
});

const stop = channelOwnerOnly((msg) => {
  const userId = String(msg.from.id);
  if (userRunningStatus[userId]) {
    userRunningStatus[userId] = false;
    clearInterval(userThreads[userId]);
    bot.sendMessage(msg.chat.id, 'Bot stopped!');
  } else {
    bot.sendMessage(msg.chat.id, 'Bot is already stopped.');
  }
});

const helpCommand = restricted((msg) => {
  const userId = String(msg.from.id);
  if (userId === OWNER_USER_ID) {
    bot.sendMessage(msg.chat.id, 'Commands:\n' +
      '/start - Start the bot\n' +
      '/stop - Stop the bot\n' +
      '/status - Check bot status\n' +
      '/setnumber <number> - Set the starting number for messages\n' +
      '/addchannel <channel_id> - Add a channel to send messages\n' +
      '/removechannel <channel_id> - Remove a channel from the list\n' +
      '/listchannels - List all added channels\n' +
      '/settarget <channel_id> - Set a specific target channel\n' +
      '/cleartarget - Clear the target channel (send to all channels)\n' +
      '/adduser <user_id> - Add an authorized user (owner only)\n' +
      '/removeuser <user_id> - Remove an authorized user (owner only)\n' +
      '/listusers - List all authorized users (owner only)\n'
    );
  } else {
    bot.sendMessage(msg.chat.id, 'Commands:\n' +
      '/start - Start the bot\n' +
      '/stop - Stop the bot\n' +
      '/status - Check bot status\n' +
      '/setnumber <number> - Set the starting number for messages\n' +
      '/addchannel <channel_id> - Add a channel to send messages\n' +
      '/removechannel <channel_id> - Remove a channel from the list\n' +
      '/listchannels - List all added channels\n' +
      '/settarget <channel_id> - Set a specific target channel\n' +
      '/cleartarget - Clear the target channel (send to all channels)\n'
    );
  }
});

const status = restricted((msg) => {
  const userId = String(msg.from.id);
  if (userRunningStatus[userId]) {
    bot.sendMessage(msg.chat.id, 'Bot is running.');
  } else {
    bot.sendMessage(msg.chat.id, 'Bot is stopped.');
  }
});

const setNumber = restricted((msg, match) => {
  const userId = String(msg.from.id);
  const number = parseInt(match[1]);
  if (!isNaN(number)) {
    userStartingNumber[userId] = number;  // Update the starting number for the user
    bot.sendMessage(msg.chat.id, `Starting number set to ${number}.`);
  } else {
    bot.sendMessage(msg.chat.id, 'Usage: /setnumber <number>');
  }
});

const addChannel = restricted((msg, match) => {
  const userId = String(msg.from.id);
  if (!userChannels[userId]) {
    userChannels[userId] = [];
  }

  const channelId = match[1];
  if (channelId && !userChannels[userId].includes(channelId)) {
    userChannels[userId].push(channelId);
    bot.sendMessage(msg.chat.id, `Channel ${channelId} added.`);
  } else {
    bot.sendMessage(msg.chat.id, `Channel ${channelId} is already in the list.`);
  }
});

const removeChannel = restricted((msg, match) => {
  const userId = String(msg.from.id);
  if (!userChannels[userId]) {
    bot.sendMessage(msg.chat.id, 'No channels found for this user.');
    return;
  }

  const channelId = match[1];
  const index = userChannels[userId].indexOf(channelId);
  if (index > -1) {
    userChannels[userId].splice(index, 1);
    bot.sendMessage(msg.chat.id, `Channel ${channelId} removed.`);
  } else {
    bot.sendMessage(msg.chat.id, `Channel ${channelId} not found in the list.`);
  }
});

const listChannels = restricted((msg) => {
  const userId = String(msg.from.id);
  if (userChannels[userId] && userChannels[userId].length) {
    bot.sendMessage(msg.chat.id, 'Added channels:\n' + userChannels[userId].join('\n'));
  } else {
    bot.sendMessage(msg.chat.id, 'No channels added.');
  }
});

const setTarget = restricted((msg, match) => {
  const userId = String(msg.from.id);
  const channelId = match[1];
  if (userChannels[userId] && userChannels[userId].includes(channelId)) {
    userTargetChannel[userId] = channelId;
    bot.sendMessage(msg.chat.id, `Target channel set to ${channelId}.`);
  } else {
    bot.sendMessage(msg.chat.id, `Channel ${channelId} not found in your list.`);
  }
});

const clearTarget = restricted((msg) => {
  const userId = String(msg.from.id);
  if (userTargetChannel[userId]) {
    delete userTargetChannel[userId];
    bot.sendMessage(msg.chat.id, 'Target channel cleared. Messages will be sent to all channels.');
  } else {
    bot.sendMessage(msg.chat.id, 'No target channel set.');
  }
});

const addUser = ownerOnly((msg, match) => {
  const userId = match[1];
  authorizedUsers.add(userId);
  bot.sendMessage(msg.chat.id, `User ${userId} authorized.`);
});

const removeUser = ownerOnly((msg, match) => {
  const userId = match[1];
  if (authorizedUsers.delete(userId)) {
    bot.sendMessage(msg.chat.id, `User ${userId} unauthorized.`);
  } else {
    bot.sendMessage(msg.chat.id, `User ${userId} not found in authorized list.`);
  }
});

const listUsers = ownerOnly((msg) => {
  if (authorizedUsers.size) {
    bot.sendMessage(msg.chat.id, 'Authorized users:\n' + Array.from(authorizedUsers).join('\n'));
  } else {
    bot.sendMessage(msg.chat.id, 'No authorized users.');
  }
});

function sendMessages(userId) {
  if (!userStartingNumber[userId]) {
    bot.sendMessage(userId, "Please set a starting number using /setnumber <number> before starting the bot.");
    userRunningStatus[userId] = false;
    clearInterval(userThreads[userId]);
    return;
  }

  let number = userStartingNumber[userId];  // Use the user's set starting number
  const choices = ["...........Big", "..........Small"];
  const colors = ["Red", "Green"];

  const targetChannel = userTargetChannel[userId];
  const channels = userChannels[userId] || [];

  const selectedText = choices[Math.floor(Math.random() * choices.length)];
  const selectedColor = colors[Math.floor(Math.random() * colors.length)];
  const message = `${number} ${selectedText} ${selectedColor}`;

  if (targetChannel) {
    if (channels.includes(targetChannel)) {
      bot.sendMessage(targetChannel, message).catch((e) => {
        console.log(`Failed to send message to ${targetChannel}: ${e}`);
      });
    } else {
      console.log(`Target channel ${targetChannel} not found in user's channel list.`);
    }
  } else {
    channels.forEach((channel) => {
      bot.sendMessage(channel, message).catch((e) => {
        console.log(`Failed to send message to ${channel}: ${e}`);
      });
    });
  }

  number += 1;
  userStartingNumber[userId] = number;  // Update the starting number for the user
}

bot.onText(/\/start/, start);
bot.onText(/\/help/, helpCommand);
bot.onText(/\/stop/, stop);
bot.onText(/\/status/, status);
bot.onText(/\/setnumber (\d+)/, setNumber);
bot.onText(/\/addchannel (.+)/, addChannel);
bot.onText(/\/removechannel (.+)/, removeChannel);
bot.onText(/\/listchannels/, listChannels);
bot.onText(/\/settarget (.+)/, setTarget);
bot.onText(/\/cleartarget/, clearTarget);
bot.onText(/\/adduser (.+)/, addUser);
bot.onText(/\/removeuser (.+)/, removeUser);
bot.onText(/\/listusers/, listUsers);
