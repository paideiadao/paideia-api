import requests
from db.schemas.dao import CreateOnChainDao
from config import Config, Network
import typing as t

def get_all_daos():
    res = requests.get(Config[Network].paideia_state+'/dao')
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)
    
def get_dao_config(daoKey: str):
    res = requests.get(Config[Network].paideia_state+'/dao/'+daoKey+'/config')
    if res.ok:
        resDict = {}
        for entry in res.json():
            resDict[entry["key"]] = {"valueType": entry["valueType"], "value": entry["value"]}
        return resDict
    else:
        raise Exception(res.text)
    
def get_dao_treasury(daoKey: str):
    res = requests.get(Config[Network].paideia_state+'/dao/'+daoKey+'/treasury')
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)
    
def get_proposals(daoKey: str):
    res = requests.get(Config[Network].paideia_state+'/dao/'+daoKey+'/proposals')
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)

def create_dao(dao: CreateOnChainDao):
    raise Exception("DAO Creation disabled until stake contract has been fixed.")
    res = requests.post(Config[Network].paideia_state+'/dao/', json={
        "name": dao.name,
        "url": dao.url,
        "description": dao.description,
        "logo": dao.design.logo,
        "banner": dao.design.banner if dao.design.banner is not None else "",
        "bannerEnabled": dao.design.banner_enabled,
        "footer": dao.design.footer if dao.design.footer is not None else "",
        "footerEnabled": dao.design.footer_enabled,
        "theme": dao.design.theme,
        "daoGovernanceTokenId": dao.tokenomics.token_id,
        "minProposalTime": dao.governance.min_proposal_time,
        "governanceType": dao.governance.governance_type,
        "quorum": dao.governance.quorum,
        "threshold": dao.governance.threshold,
        "pureParticipationWeight": dao.governance.pure_participation_weight,
        "participationWeight": dao.governance.participation_weight,
        "stakePoolSize": dao.tokenomics.staking_config.stake_pool_size,
        "stakingEmissionAmount": dao.tokenomics.staking_config.staking_emission_amount,
        "stakingEmissionDelay": dao.tokenomics.staking_config.staking_emission_delay,
        "stakingCycleLength": dao.tokenomics.staking_config.staking_cycle_length,
        "stakingProfitSharePct": dao.tokenomics.staking_config.staking_profit_share_pct,
        "userAddresses": dao.user_addresses,
    })
    if res.ok:
        return res.json()
    else:
        raise Exception(res.text)
