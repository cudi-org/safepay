// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
}

contract BulutPaymentHubV2 {
    
    IERC20 public immutable usdcToken;
    address public immutable keeperAddress;

    enum SubscriptionStatus {Active, Paused, Cancelled}

    struct Subscription {
        address subscriber;
        address recipient;
        uint256 amount;
        string frequency;
        uint256 startDate;
        SubscriptionStatus status;
        uint256 lastPaymentDate;
    }

    struct RecipientSplit {
        address recipientAddress;
        uint256 percentageBasisPoints;
    }

    mapping(bytes32 => Subscription) public subscriptions;

    modifier onlyKeeper() {
        require(msg.sender == keeperAddress, "Only the CUDI Keeper address can execute payments.");
        _;
    }

    constructor(address _usdcTokenAddress, address _keeperAddress) {
        require(_usdcTokenAddress != address(0), "Invalid token address");
        require(_keeperAddress != address(0), "Invalid keeper address");
        usdcToken = IERC20(_usdcTokenAddress);
        keeperAddress = _keeperAddress;
    }

    event SubscriptionCreated(
        bytes32 indexed subscriptionId,
        address indexed subscriber,
        address recipient,
        uint256 amount,
        string frequency
    );

    event PaymentSplitIntent(
        bytes32 indexed splitId,
        address indexed payer,
        uint256 totalAmount
    );
    
    event SubscriptionExecuted(
        bytes32 indexed subscriptionId,
        address indexed payer,
        uint256 amount,
        uint256 timestamp
    );

    function createSubscription(
        address _recipient,
        uint256 _amount,
        string memory _frequency,
        uint256 _startDate
    ) public returns (bytes32 subscriptionId) {
        require(_amount > 0, "Amount must be greater than zero.");
        
        subscriptionId = keccak256(
            abi.encodePacked(msg.sender, _recipient, _amount, _frequency, _startDate, block.timestamp)
        );

        subscriptions[subscriptionId] = Subscription({
            subscriber: msg.sender,
            recipient: _recipient,
            amount: _amount,
            frequency: _frequency,
            startDate: _startDate,
            status: SubscriptionStatus.Active,
            lastPaymentDate: 0
        });

        emit SubscriptionCreated(
            subscriptionId,
            msg.sender,
            _recipient,
            _amount,
            _frequency
        );
    }

    function splitPayment(
        uint256 _totalAmount,
        RecipientSplit[] memory _recipients,
        string memory _memo
    ) public returns (bytes32 splitId) {
        require(_recipients.length > 0, "Recipients list cannot be empty.");
        require(_totalAmount > 0, "Total amount must be greater than zero.");

        uint256 totalPercentage = 0;
        for (uint256 i = 0; i < _recipients.length; i++) {
            totalPercentage += _recipients[i].percentageBasisPoints;
        }

        require(totalPercentage == 10000, "Recipient percentages must sum to 100%");

        splitId = keccak256(abi.encodePacked(msg.sender, _totalAmount, _recipients.length, block.timestamp, _memo));

        emit PaymentSplitIntent(splitId, msg.sender, _totalAmount);
    }
    
    function executeSubscriptionPayment(bytes32 _subscriptionId) public onlyKeeper returns (bool success) {
        Subscription storage s = subscriptions[_subscriptionId];
        
        require(s.status == SubscriptionStatus.Active, "Subscription not active");
        
        success = usdcToken.transferFrom(s.subscriber, s.recipient, s.amount);
        require(success, "Failed to transfer funds. Check allowance or balance.");

        s.lastPaymentDate = block.timestamp;

        emit SubscriptionExecuted(_subscriptionId, s.subscriber, s.amount, block.timestamp);
        return true;
    }
}
